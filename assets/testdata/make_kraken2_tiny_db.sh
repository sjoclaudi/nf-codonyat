#!/usr/bin/env bash
# Rebuild assets/testdata/kraken2_tiny_db: a ~110 KB Kraken2 database for CI only.
# Library: HIV-1 HXB2 (K03455, taxid 11676), phiX174 (NC_001422.1, taxid 10847),
# human mitochondrion (NC_012920.1, taxid 9606), with a minimal hand-written taxonomy.
# Real runs use a prebuilt index such as Kraken2 Standard-8 (see README).
# Requires docker (or a local kraken2 2.1.6), curl and python3.
set -euo pipefail
cd "$(dirname "$0")"
IMG=community.wave.seqera.io/library/kraken2_coreutils_pigz:920ecc6b96e2ba71
tmp=$(mktemp -d)
for acc in NC_001422.1 NC_012920.1; do
    curl -fsSL "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=${acc}&rettype=fasta&retmode=text" -o "$tmp/$acc.fa"
done
mkdir -p "$tmp/db/taxonomy"
python3 - "$tmp" <<'PY'
import sys
tmp = sys.argv[1]
nodes = [(1, 1, "no rank"), (10239, 1, "superkingdom"), (2, 1, "superkingdom"), (2759, 1, "superkingdom"),
         (11676, 10239, "species"), (10847, 10239, "species"), (9606, 2759, "species")]
names = {1: "root", 10239: "Viruses", 2: "Bacteria", 2759: "Eukaryota",
         11676: "Human immunodeficiency virus 1", 10847: "Escherichia phage phiX174", 9606: "Homo sapiens"}
with open(f"{tmp}/db/taxonomy/nodes.dmp", "w") as f:
    for t, p, r in nodes:
        f.write(f"{t}\t|\t{p}\t|\t{r}\t|\t\t|\t0\t|\t0\t|\t11\t|\t0\t|\t0\t|\t0\t|\t0\t|\t0\t|\t\t|\n")
with open(f"{tmp}/db/taxonomy/names.dmp", "w") as f:
    for t, n in names.items():
        f.write(f"{t}\t|\t{n}\t|\t\t|\tscientific name\t|\n")
def seq(path):
    return "".join(l.strip() for l in open(path) if not l.startswith(">"))
with open(f"{tmp}/library.fa", "w") as f:
    f.write(f">K03455.1|kraken:taxid|11676\n{seq('reference.fasta')}\n")
    f.write(f">NC_001422.1|kraken:taxid|10847\n{seq(tmp + '/NC_001422.1.fa')}\n")
    f.write(f">NC_012920.1|kraken:taxid|9606\n{seq(tmp + '/NC_012920.1.fa')}\n")
PY
docker run --rm -u "$(id -u):$(id -g)" -v "$tmp:/w" -w /w "$IMG" bash -c \
    "kraken2-build --add-to-library library.fa --db db --no-masking && kraken2-build --build --db db --threads 2 && kraken2-build --clean --db db"
mkdir -p kraken2_tiny_db
cp "$tmp"/db/*.k2d kraken2_tiny_db/
rm -rf "$tmp"
