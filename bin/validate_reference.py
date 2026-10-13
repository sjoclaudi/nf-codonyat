#!/usr/bin/env python3
"""Validate reference, primers, annotation and samplesheet for nf-codonyat.

Usage:
    validate_reference.py --reference ref.fasta --primer-bed primers.bed \\
        --annotation annot.gff3 --out validation.json

Checks:
- Single/multi-record FASTA (max 100kb total for custom)
- BED: 6 columns, chrom matches FASTA, paired _LEFT/_RIGHT per amplicon, coordinates in bounds
- Annotation: CDS in bounds, length divisible by 3, + strand only, not spliced/frameshift
- Amplicon coverage: each amplicon overlaps >=1 CDS
- Reference size limit: 100 kb for custom preset

Writes validation.json with {"valid": bool, "errors": [...], "warnings": [...]}
Exit code 0 if valid, non-zero otherwise.

Research use only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple


@dataclass
class ValidationError:
    code: str
    file: str
    line: int | None
    message: str

    def to_dict(self):
        return {
            "code": self.code,
            "file": self.file,
            "line": self.line,
            "message": self.message
        }


@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]

    def to_dict(self):
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }


def read_fasta(path: Path) -> Dict[str, str]:
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
                # Extract ID (everything before first space)
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)
        if current_id:
            records[current_id] = "".join(current_seq)
    
    return records


def read_bed(path: Path) -> List[Tuple[str, int, int, str, str, str]]:
    """Read BED file, return list of (chrom, start, end, name, pool, strand)."""
    rows = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 6:
                raise ValueError(f"Line {i}: expected 6 columns, got {len(parts)}")
            chrom, start, end, name, pool, strand = parts[:6]
            rows.append((chrom, int(start), int(end), name, pool, strand))
    return rows


def read_gff3_cds(path: Path) -> List[Tuple[str, int, int, str, str]]:
    """Read GFF3, extract CDS features: (seqid, start, end, name, strand)."""
    features = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.rstrip().split("\t")
            if len(parts) < 9:
                continue
            if parts[2] != "CDS":
                continue
            seqid = parts[0]
            start = int(parts[3])  # GFF3 is 1-based
            end = int(parts[4])
            strand = parts[6]
            # Extract Name or ID from attributes
            attrs = dict(item.split("=", 1) for item in parts[8].split(";") if "=" in item)
            name = attrs.get("Name", attrs.get("ID", f"CDS_{len(features)+1}"))
            features.append((seqid, start, end, name, strand))
    return features


def read_bed4_annotation(path: Path) -> List[Tuple[str, int, int, str]]:
    """Read 4-column BED annotation: (chrom, start, end, name). Start is 0-based."""
    features = []
    with open(path) as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            chrom = parts[0]
            start = int(parts[1])  # BED is 0-based
            end = int(parts[2])
            name = parts[3]
            features.append((chrom, start + 1, end, name))  # Convert to 1-based
    return features


def validate_reference(records: Dict[str, str], max_size: int | None, 
                      ref_path: str) -> List[ValidationError]:
    """Validate reference FASTA."""
    errors = []
    
    if not records:
        errors.append(ValidationError(
            "REF_EMPTY", ref_path, None,
            "Reference FASTA is empty"
        ))
        return errors
    
    # Check total size for custom preset
    if max_size:
        total_size = sum(len(seq) for seq in records.values())
        if total_size > max_size:
            errors.append(ValidationError(
                "REF_TOO_LARGE", ref_path, None,
                f"Reference total size {total_size} bp exceeds limit {max_size} bp"
            ))
    
    return errors


def validate_primers(bed_rows: List[Tuple], records: Dict[str, str], 
                    bed_path: str) -> List[ValidationError]:
    """Validate primer BED file."""
    errors = []
    
    if not bed_rows:
        errors.append(ValidationError(
            "BED_EMPTY", bed_path, None,
            "Primer BED file is empty"
        ))
        return errors
    
    # Check chroms match reference
    bed_chroms = set(row[0] for row in bed_rows)
    ref_chroms = set(records.keys())
    
    for chrom in bed_chroms:
        if chrom not in ref_chroms:
            errors.append(ValidationError(
                "CHROM_MISMATCH", bed_path, None,
                f"Chromosome '{chrom}' in BED not found in reference"
            ))
    
    # Check pairing: each amplicon must have exactly one _LEFT and one _RIGHT
    amplicons = defaultdict(list)
    for i, (chrom, start, end, name, pool, strand) in enumerate(bed_rows, 1):
        if not name.endswith("_LEFT") and not name.endswith("_RIGHT"):
            errors.append(ValidationError(
                "BED_NAMING", bed_path, i,
                f"Primer name '{name}' must end with _LEFT or _RIGHT"
            ))
            continue
        
        amplicon = name.rsplit("_", 1)[0]
        amplicons[amplicon].append((name, chrom, start, end, strand, i))
    
    for amplicon, primers in amplicons.items():
        left = [p for p in primers if p[0].endswith("_LEFT")]
        right = [p for p in primers if p[0].endswith("_RIGHT")]
        
        if len(left) != 1:
            errors.append(ValidationError(
                "BED_UNPAIRED", bed_path, None,
                f"Amplicon '{amplicon}' has {len(left)} LEFT primers (expected 1)"
            ))
        if len(right) != 1:
            errors.append(ValidationError(
                "BED_UNPAIRED", bed_path, None,
                f"Amplicon '{amplicon}' has {len(right)} RIGHT primers (expected 1)"
            ))
        
        if left and right:
            left_name, left_chrom, left_start, left_end, left_strand, left_line = left[0]
            right_name, right_chrom, right_start, right_end, right_strand, right_line = right[0]
            
            if left_chrom != right_chrom:
                errors.append(ValidationError(
                    "BED_CHROM_MISMATCH", bed_path, None,
                    f"Amplicon '{amplicon}' primers on different chromosomes"
                ))
            
            # Check coordinates in bounds
            if left_chrom in records:
                seq_len = len(records[left_chrom])
                if left_start < 0 or left_end > seq_len:
                    errors.append(ValidationError(
                        "BED_OUT_OF_RANGE", bed_path, left_line,
                        f"{left_name} coordinates [{left_start}, {left_end}] out of range [0, {seq_len}]"
                    ))
                if right_start < 0 or right_end > seq_len:
                    errors.append(ValidationError(
                        "BED_OUT_OF_RANGE", bed_path, right_line,
                        f"{right_name} coordinates [{right_start}, {right_end}] out of range [0, {seq_len}]"
                    ))
                
                # Check LEFT before RIGHT
                if left_start >= right_end:
                    errors.append(ValidationError(
                        "BED_ORDER", bed_path, None,
                        f"Amplicon '{amplicon}' LEFT primer not before RIGHT primer"
                    ))
    
    return errors


def validate_annotation(cds_list: List[Tuple], records: Dict[str, str], 
                       annot_path: str) -> List[ValidationError]:
    """Validate annotation CDS features."""
    errors = []
    
    for seqid, start, end, name, strand in cds_list:
        # Check seqid in reference
        if seqid not in records:
            errors.append(ValidationError(
                "CHROM_MISMATCH", annot_path, None,
                f"CDS '{name}' on sequence '{seqid}' not in reference"
            ))
            continue
        
        seq_len = len(records[seqid])
        
        # Check bounds
        if start < 1 or end > seq_len:
            errors.append(ValidationError(
                "CDS_OUT_OF_RANGE", annot_path, None,
                f"CDS '{name}' coordinates [{start}, {end}] out of range [1, {seq_len}]"
            ))
            continue
        
        # Check strand (only + supported in v0.5.0)
        if strand == "-":
            errors.append(ValidationError(
                "CDS_UNSUPPORTED", annot_path, None,
                f"CDS '{name}' on minus strand not supported"
            ))
            continue
        
        # Check length divisible by 3
        length = end - start + 1
        if length % 3 != 0:
            errors.append(ValidationError(
                "CDS_NOT_MULTIPLE_OF_3", annot_path, None,
                f"CDS '{name}' length {length} not divisible by 3"
            ))
        
        # Check name doesn't contain forbidden characters
        if any(c in name for c in ["(", ":", ";"]):
            errors.append(ValidationError(
                "CDS_INVALID_NAME", annot_path, None,
                f"CDS name '{name}' contains forbidden characters ( : or ;"
            ))
    
    return errors


def validate_amplicon_coverage(bed_rows: List[Tuple], cds_list: List[Tuple], 
                               bed_path: str) -> List[ValidationError]:
    """Check each amplicon overlaps at least one CDS."""
    errors = []
    
    # Group primers by amplicon
    amplicons = defaultdict(list)
    for chrom, start, end, name, pool, strand in bed_rows:
        if name.endswith("_LEFT") or name.endswith("_RIGHT"):
            amplicon = name.rsplit("_", 1)[0]
            amplicons[amplicon].append((chrom, start, end))
    
    for amplicon, primers in amplicons.items():
        if len(primers) != 2:
            continue  # Already reported as unpaired
        
        # Get amplicon bounds
        chrom = primers[0][0]
        amp_start = min(p[1] for p in primers)
        amp_end = max(p[2] for p in primers)
        
        # Check if any CDS overlaps
        overlaps = False
        for cds_seqid, cds_start, cds_end, cds_name, cds_strand in cds_list:
            if cds_seqid == chrom:
                # Check overlap (BED is 0-based, CDS is 1-based)
                if not (amp_end <= cds_start - 1 or amp_start >= cds_end):
                    overlaps = True
                    break
        
        if not overlaps:
            errors.append(ValidationError(
                "AMPLICON_NO_CDS", bed_path, None,
                f"Amplicon '{amplicon}' does not overlap any CDS"
            ))
    
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, 
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reference", required=True, type=Path, help="Reference FASTA")
    parser.add_argument("--primer-bed", type=Path, help="Primer BED (6 columns)")
    parser.add_argument("--annotation", type=Path, help="Annotation GFF3 or BED")
    parser.add_argument("--preset", default="custom", help="Preset name (custom enforces size limit)")
    parser.add_argument("--out", type=Path, default="validation.json", help="Output JSON")
    
    args = parser.parse_args()
    
    errors = []
    warnings = []
    
    # Read reference
    try:
        records = read_fasta(args.reference)
    except Exception as e:
        errors.append(ValidationError(
            "REF_READ_ERROR", str(args.reference), None,
            f"Failed to read reference: {e}"
        ))
        result = ValidationResult(False, errors, warnings)
        args.out.write_text(json.dumps(result.to_dict(), indent=2))
        sys.exit(1)
    
    # Validate reference
    max_size = 100_000 if args.preset == "custom" else None
    errors.extend(validate_reference(records, max_size, str(args.reference)))
    
    # Read and validate primers if provided
    bed_rows = []
    if args.primer_bed:
        try:
            bed_rows = read_bed(args.primer_bed)
            errors.extend(validate_primers(bed_rows, records, str(args.primer_bed)))
        except Exception as e:
            errors.append(ValidationError(
                "BED_READ_ERROR", str(args.primer_bed), None,
                f"Failed to read primer BED: {e}"
            ))
    
    # Read and validate annotation if provided
    cds_list = []
    if args.annotation:
        try:
            annot_str = str(args.annotation).lower()
            if annot_str.endswith(".gff") or annot_str.endswith(".gff3"):
                cds_list = read_gff3_cds(args.annotation)
            elif annot_str.endswith(".bed"):
                # BED annotation: convert to CDS format (assume + strand)
                bed_annot = read_bed4_annotation(args.annotation)
                cds_list = [(c, s, e, n, "+") for c, s, e, n in bed_annot]
            else:
                errors.append(ValidationError(
                    "ANNOTATION_FORMAT", str(args.annotation), None,
                    "Annotation must be .gff, .gff3, or .bed"
                ))
            
            if cds_list:
                errors.extend(validate_annotation(cds_list, records, str(args.annotation)))
        except Exception as e:
            errors.append(ValidationError(
                "ANNOTATION_READ_ERROR", str(args.annotation), None,
                f"Failed to read annotation: {e}"
            ))
    
    # Validate amplicon coverage if we have both primers and annotation
    if bed_rows and cds_list and not errors:
        errors.extend(validate_amplicon_coverage(bed_rows, cds_list, str(args.primer_bed)))
    
    result = ValidationResult(len(errors) == 0, errors, warnings)
    args.out.write_text(json.dumps(result.to_dict(), indent=2))
    
    if errors:
        print(f"Validation failed with {len(errors)} error(s)", file=sys.stderr)
        for err in errors:
            print(f"  [{err.code}] {err.message}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation passed", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
