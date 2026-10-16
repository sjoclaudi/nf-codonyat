#!/usr/bin/env python3
"""Build tiny non-HIV custom-mode datasets for nf-codonyat (deterministic).
Sequences: NCBI nuccore efetch (MN908947.3, NC_002017.1, NC_002018.1) in --src.
Primers: ARTIC nCoV-2019 V4.1 (CC BY 4.0) for SARS-CoV-2; hand-made pairs for influenza.
Reads: synthetic 2x250 amplicon pairs (R1 from LEFT primer, R2 from RIGHT primer),
first k of n pairs carry the listed changes. Research use only."""
import argparse, gzip, collections
from pathlib import Path

RL = 250
COMP = str.maketrans("ACGTN", "TGCAN")
rc = lambda s: s.translate(COMP)[::-1]

def fasta(p):
    l = Path(p).read_text().splitlines()
    return l[0][1:].split()[0], "".join(l[1:]).upper()

def wrap(rid, s):
    return f">{rid}\n" + "\n".join(s[i:i+70] for i in range(0, len(s), 70)) + "\n"

def amplicons(bed):
    d = collections.defaultdict(lambda: collections.defaultdict(list))
    for l in Path(bed).read_text().splitlines():
        c, s, e, n = l.split("\t")[:4]
        amp, side = n.rsplit("_", 1)
        d[amp][side].append((c, int(s), int(e)))
    return {a: (v["LEFT"][0][0], min(x[1] for x in v["LEFT"]), max(x[2] for x in v["RIGHT"])) for a, v in d.items()}

def simulate(out, seqs, amps, plan):
    """plan: list of (amp, n_pairs, n_mut, {pos1: base})"""
    r1, r2 = [], []
    for amp, n, k, changes in plan:
        chrom, s0, e = amps[amp]
        ref = seqs[chrom]
        mut = list(ref)
        for p, b in changes.items():
            mut[p-1] = b
        mut = "".join(mut)
        for i in range(n):
            src = mut if i < k else ref
            frag = src[s0:e]
            # No "_<digits>" suffix: codonyat 1.3.1 only treats that as a collapsed-read count with --collapsed-read-counts.
            name = f"@sim:{amp}:r{i}"
            a, b = frag[:RL], rc(frag)[:RL]
            if i % 2:  # half the pairs start on the reverse strand (real ligation libraries)
                a, b = b, a
            q = "I" * min(RL, len(frag))
            r1 += [f"{name}/1", a, "+", q]
            r2 += [f"{name}/2", b, "+", q]
    for fn, recs in ((f"{out}_R1.fastq.gz", r1), (f"{out}_R2.fastq.gz", r2)):
        with gzip.GzipFile(fn, "wb", mtime=0) as fh:
            fh.write(("\n".join(recs)+"\n").encode())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", required=True); ap.add_argument("--artic-bed", required=True)
    a = ap.parse_args(); src = Path(a.src)
    here = Path(__file__).resolve().parent

    # SARS-CoV-2: plain (unannotated) FASTA + GFF3 (all 11 NCBI CDS, ORF1ab joined) + ARTIC V4.1 BED
    d = here/"sarscov2"; d.mkdir(exist_ok=True)
    rid, seq = fasta(src/"MN908947.3.fa")
    (d/"reference.fasta").write_text(wrap(rid, seq))
    (d/"primers.bed").write_text(Path(a.artic_bed).read_text())
    gff = ["##gff-version 3", f"##sequence-region {rid} 1 {len(seq)}"]
    # NCBI MN908947.3 CDS set. ORF1ab = two CDS rows sharing one ID (-1 frameshift at 13468).
    # Every ARTIC amplicon overlaps a CDS (AMPLICON_NO_CDS is a warning); all CDS are listed so the test has 0 warnings.
    cds = (("ORF1ab", 266, 13468), ("ORF1ab", 13468, 21555), ("S", 21563, 25384), ("ORF3a", 25393, 26220),
           ("E", 26245, 26472), ("M", 26523, 27191), ("ORF6", 27202, 27387), ("ORF7a", 27394, 27759),
           ("ORF7b", 27756, 27887), ("ORF8", 27894, 28259), ("N", 28274, 29533), ("ORF10", 29558, 29674))
    for g, s, e in cds:
        gff.append(f"{rid}\tGenBank\tCDS\t{s}\t{e}\t.\t+\t0\tID=cds-{g};gene={g}")
    (d/"annotation.gff3").write_text("\n".join(gff)+"\n")
    amps = amplicons(d/"primers.bed")
    simulate(d/"SARS2_SIM", {rid: seq}, amps, [
        ("SARS-CoV-2_78", 200, 140, {23403: "G"}),                       # S D614G 70%
        ("SARS-CoV-2_96", 200, 80, {28881: "A", 28882: "A", 28883: "C"}), # N R203K/G204R 40%
        ("SARS-CoV-2_87", 100, 0, {}),                                   # E start, reference only
    ])
    (d/"samplesheet.csv").write_text("sample,fastq_1,fastq_2,sam\nSARS2_SIM,SARS2_SIM_R1.fastq.gz,SARS2_SIM_R2.fastq.gz,\n")

    # Influenza A/PR/8/34: two-record FASTA (HA seg 4, NA seg 6) + 4-col BED annotation + 2 primer pairs
    d = here/"influenza"; d.mkdir(exist_ok=True)
    ha_id, ha = fasta(src/"NC_002017.1.fa"); na_id, na = fasta(src/"NC_002018.1.fa")
    (d/"reference.fasta").write_text(wrap(ha_id, ha) + wrap(na_id, na))
    (d/"annotation.bed").write_text(f"{ha_id}\t32\t1733\tHA\n{na_id}\t20\t1385\tNA\n")
    (d/"primers.bed").write_text(
        f"{ha_id}\t32\t52\tFLUA_HA_1_LEFT\t1\t+\n{ha_id}\t399\t419\tFLUA_HA_1_RIGHT\t1\t-\n"
        f"{na_id}\t20\t40\tFLUA_NA_1_LEFT\t1\t+\n{na_id}\t379\t399\tFLUA_NA_1_RIGHT\t1\t-\n")
    amps = amplicons(d/"primers.bed")
    simulate(d/"FLU_SIM", {ha_id: ha, na_id: na}, amps, [
        ("FLUA_HA_1", 200, 50, {45: "G"}),   # HA codon 5 CTA>GTA (L5V) 25%
        ("FLUA_NA_1", 100, 60, {27: "G"}),   # NA codon 3 CCA>GCA (P3A) 60%
    ])
    (d/"samplesheet.csv").write_text("sample,fastq_1,fastq_2,sam\nFLU_SIM,FLU_SIM_R1.fastq.gz,FLU_SIM_R2.fastq.gz,\n")

if __name__ == "__main__":
    main()
