#!/usr/bin/env python3
"""Write consensus_rules.sam: a small synthetic SAM that exercises the consensus rules.

Reads are exact copies of the HXB2 reference (assets/testdata/reference.fasta), except:
  * 200 reads cover 2551-2700 (1-based): at 2600, 45% A / 45% G / 10% T  -> IUPAC 'R'
    (no single base reaches the 0.5 threshold; A+G does)
  * 140 of those 200 reads (70%) carry a 3-bp deletion of 2650-2652      -> deletion applied
  * 50 reads cover 2801-2950 (depth 50 < 100)                             -> 'N'
Everything else has depth 0 -> 'N'.

    python3 make_consensus_testdata.py   # writes consensus_rules.sam next to this script
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    lines = (HERE / "reference.fasta").read_text().splitlines()
    ref_name = lines[0][1:].split()[0]
    ref = "".join(lines[1:]).upper()
    out = [f"@HD\tVN:1.6\tSO:unsorted", f"@SQ\tSN:{ref_name}\tLN:{len(ref)}"]

    def add(name: str, pos: int, seq: str, cigar: str) -> None:
        out.append("\t".join([name, "0", ref_name, str(pos), "60", cigar, "*", "0", "0", seq, "I" * len(seq)]))

    start = 2551
    for i in range(200):
        base = "A" if i < 90 else ("G" if i < 180 else "T")
        if i % 10 < 7:   # 70% carry the deletion of 2650-2652
            left = ref[start - 1:2649]          # 2551..2649 (99 bases)
            right = ref[2652:2652 + 51]          # 2653..2703 (51 bases)
            seq, cigar = left + right, "99M3D51M"
        else:
            seq, cigar = ref[start - 1:start - 1 + 150], "150M"
        seq = seq[:2600 - start] + base + seq[2600 - start + 1:]
        add(f"cons_hi_{i}", start, seq, cigar)
    for i in range(50):
        add(f"cons_lo_{i}", 2801, ref[2800:2950], "150M")
    (HERE / "consensus_rules.sam").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
