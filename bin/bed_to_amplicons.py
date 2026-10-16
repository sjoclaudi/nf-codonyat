#!/usr/bin/env python3
"""Convert 6-column primer BED to amplicons TSV with sequences extracted from reference.

Usage:
    bed_to_amplicons.py --reference ref.fasta --primer-bed primers.bed --out amplicons.tsv

Reads primers.bed with columns: chrom, start, end, name, pool, strand
Name format: <amplicon>_LEFT or <amplicon>_RIGHT
Extracts primer sequences from the reference and writes 7-column amplicons TSV.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path


def read_fasta(path: Path) -> dict:
    """Read FASTA and return {id: sequence}."""
    records = {}
    current_id = None
    current_seq = []
    
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if line.startswith(">"):
                if current_id:
                    records[current_id] = "".join(current_seq)
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
        if current_id:
            records[current_id] = "".join(current_seq)
    
    return records


def read_bed(path: Path) -> list:
    """Read BED file, return list of (chrom, start, end, name, pool, strand)."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                print(f"Warning: skipping line with {len(parts)} columns: {line}", file=sys.stderr)
                continue
            chrom, start, end, name, pool, strand = parts[:6]
            rows.append((chrom, int(start), int(end), name, pool, strand))
    return rows


def extract_sequence(seq: str, start: int, end: int, strand: str) -> str:
    """Extract sequence from reference. BED is 0-based, half-open."""
    subseq = seq[start:end]
    if strand == "-":
        # Reverse complement
        complement = str.maketrans("ACGTacgt", "TGCAtgca")
        subseq = subseq.translate(complement)[::-1]
    return subseq.upper()


def bed_to_amplicons(reference: dict, bed_rows: list) -> list:
    """Convert primer BED to amplicons TSV format."""
    # Group primers by amplicon
    amplicons = defaultdict(list)
    for chrom, start, end, name, pool, strand in bed_rows:
        if not (name.endswith("_LEFT") or name.endswith("_RIGHT")):
            print(f"Warning: primer name '{name}' doesn't end with _LEFT or _RIGHT, skipping", file=sys.stderr)
            continue
        
        amplicon = name.rsplit("_", 1)[0]
        primer_type = name.rsplit("_", 1)[1]
        amplicons[amplicon].append((chrom, start, end, primer_type, pool, strand))
    
    results = []
    for amplicon, primers in sorted(amplicons.items()):
        left = [p for p in primers if p[3] == "LEFT"]
        right = [p for p in primers if p[3] == "RIGHT"]
        
        if len(left) != 1 or len(right) != 1:
            print(f"Warning: amplicon '{amplicon}' doesn't have exactly 1 LEFT and 1 RIGHT primer, skipping", file=sys.stderr)
            continue
        
        left_chrom, left_start, left_end, _, left_pool, left_strand = left[0]
        right_chrom, right_start, right_end, _, right_pool, right_strand = right[0]
        
        if left_chrom != right_chrom:
            print(f"Warning: amplicon '{amplicon}' primers on different chromosomes, skipping", file=sys.stderr)
            continue
        
        if left_chrom not in reference:
            print(f"Warning: chromosome '{left_chrom}' not found in reference, skipping amplicon '{amplicon}'", file=sys.stderr)
            continue
        
        # Extract primer sequences
        seq = reference[left_chrom]
        left_seq = extract_sequence(seq, left_start, left_end, left_strand)
        right_seq = extract_sequence(seq, right_start, right_end, right_strand)
        
        # Amplicon coordinates: from left primer end to right primer start (1-based, inclusive)
        # BED is 0-based half-open, so left_end is already the base after the primer
        # right_start is the first base of the right primer
        amp_start = left_end + 1  # Convert to 1-based
        amp_end = right_start      # Already 0-based, becomes 1-based inclusive
        
        # For the TSV, we need to determine which protein this amplicon covers
        # For now, set protein to "unknown" - the user or preset should specify this
        # In practice, presets will provide amplicons directly or annotation will be used
        
        results.append({
            "label": amplicon,
            "protein": "all",  # Default to all proteins
            "reference": left_chrom,
            "5p_seq": left_seq,
            "3p_seq": right_seq,
            "start": amp_start,
            "end": amp_end
        })
    
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, 
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference", required=True, type=Path, help="Reference FASTA")
    parser.add_argument("--primer-bed", required=True, type=Path, help="6-column primer BED")
    parser.add_argument("--out", required=True, type=Path, help="Output amplicons TSV")
    
    args = parser.parse_args()
    
    # Read reference
    reference = read_fasta(args.reference)
    print(f"Read {len(reference)} sequence(s) from {args.reference}", file=sys.stderr)
    
    # Read BED
    bed_rows = read_bed(args.primer_bed)
    print(f"Read {len(bed_rows)} primers from {args.primer_bed}", file=sys.stderr)
    
    # Convert
    amplicons = bed_to_amplicons(reference, bed_rows)
    print(f"Generated {len(amplicons)} amplicons", file=sys.stderr)
    
    # Write TSV
    with open(args.out, "w") as f:
        f.write("label\tprotein\treference\t5p_seq\t3p_seq\tstart\tend\n")
        for amp in amplicons:
            f.write(f"{amp['label']}\t{amp['protein']}\t{amp['reference']}\t"
                   f"{amp['5p_seq']}\t{amp['3p_seq']}\t{amp['start']}\t{amp['end']}\n")
    
    print(f"Wrote amplicons TSV to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
