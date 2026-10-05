#!/usr/bin/env python3
# Usage: python3 docs/images/make_metro_map.py docs/images/nf-codonyat-metro-map.svg
# PNG (2x): cairosvg docs/images/nf-codonyat-metro-map.svg -o docs/images/nf-codonyat-metro-map.png -s 2
"""Generate the nf-codonyat metro map SVG (hand-laid, nf-core metro style)."""
import sys

W, H = 2120, 880
FONT = "'Helvetica Neue', Helvetica, Arial, 'DejaVu Sans', sans-serif"
C = dict(fastq="#1f77b4", sam="#7b3fa0", contam="#d62728", subtype="#2ca02c",
         strand="#ff7f0e", consensus="#17a2a2")
LW = 7
OFF = 9           # spacing of parallel lines in a bundle
R = 11            # station radius

Y_CON, Y_SUB, Y_STR, Y_TRK, Y_LOW = 195, 310, 425, 510, 660
# bundle offsets on the trunk (FASTQ lines share Input -> FastQC -> fastp)
B = dict(fastq=Y_TRK, strand=Y_TRK - OFF, subtype=Y_TRK - 2 * OFF, contam=Y_TRK - 3 * OFF)
VX = dict(contam=410, subtype=410 + OFF, strand=410 + 2 * OFF)   # vertical turn-up x

out = []
def add(s): out.append(s)

def text(x, y, s, size=15, anchor="middle", weight="normal", fill="#222", style=""):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    add(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" {style}>{s}</text>')

def line(pts, color, dash=None):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{LW}" stroke-linejoin="round" stroke-linecap="round"{da}/>')

def station(x, y):
    add(f'<circle cx="{x}" cy="{y}" r="{R}" fill="#fff" stroke="#222" stroke-width="3"/>')

def pill(x, y0, y1, w=2 * R):
    add(f'<rect x="{x - w/2}" y="{y0 - R}" width="{w}" height="{y1 - y0 + 2*R}" rx="{w/2}" fill="#fff" stroke="#222" stroke-width="3"/>')

def terminus(x, y0, y1):
    add(f'<rect x="{x - 9}" y="{y0 - 13}" width="18" height="{y1 - y0 + 26}" rx="4" fill="#222"/>')

def label(x, y, main, sub=None, pos="below", anchor="middle"):
    if pos == "below":
        text(x, y + R + 20, main, 15, anchor, "bold")
        if sub: text(x, y + R + 38, sub, 12.5, anchor, fill="#555")
    else:   # above
        if sub:
            text(x, y - R - 26, main, 15, anchor, "bold")
            text(x, y - R - 9, sub, 12.5, anchor, fill="#555")
        else:
            text(x, y - R - 10, main, 15, anchor, "bold")

def section(x0, y0, x1, y1, name, note=None, bottom=False):
    add(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="10" fill="#f3f5f8" stroke="#c9d1db" stroke-width="1.5"/>')
    t = name.upper()
    ty = y1 - 9 if bottom else y0 + 18
    text(x0 + 10, ty, t, 12.5, "start", "bold", "#5a6675", 'letter-spacing="1.2"')
    if note:
        nx = x0 + 10 + len(t) * 9.6 + 10
        text(nx, ty, note, 12, "start", "normal", "#7a8592", 'font-style="italic"')

# ---------------------------------------------------------------- stations x
X = dict(inp=95, fastqc=225, fastp=345,
         bbmerge=560, bt2=700, smerge=840, flag1=980, filt=1120, flag2=1260,
         cdy=1400, aa=1540, summ=1680, mqc=1855, prov=1990, end=2070)

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
text(40, 50, "nf-codonyat", 34, "start", "bold")
text(40, 80, "codon-aware amino acid variant typing of HIV-1 amplicon NGS data (FASTQ or SAM)", 17, "start", fill="#555")

# ---------------------------------------------------------------- sections
section(40, 455, 158, 750, "Input", bottom=True)
section(170, 455, 395, 590, "Pre-processing / QC", bottom=True)
section(500, 110, 920, 220, "Contamination", "Kraken2 · report only")
section(500, 225, 920, 335, "Subtyping", "BBSplit read mapping · report only")
section(640, 340, 1470, 450, "Strand branch", "PE pairs · --strand_metrics_unmerged")
section(500, 455, 1325, 590, "Merge + alignment", "SAM samples join at flagstat", bottom=True)
section(1335, 455, 1750, 590, "Codon / AA tables", bottom=True)
section(1140, 610, 1610, 740, "Consensus", "iVar · --skip_consensus")
section(1785, 110, 2105, 590, "Reporting", bottom=True)

# ---------------------------------------------------------------- lines
# contamination: bundle -> vertical -> row -> MultiQC
line([(X["inp"], B["contam"]), (VX["contam"], B["contam"]), (VX["contam"], Y_CON), (X["mqc"], Y_CON)], C["contam"])
line([(X["inp"], B["subtype"]), (VX["subtype"], B["subtype"]), (VX["subtype"], Y_SUB), (X["mqc"], Y_SUB)], C["subtype"])
# strand: bundle -> row -> descend 45 deg into codon->AA table
d = Y_TRK - Y_STR
line([(X["inp"], B["strand"]), (VX["strand"], B["strand"]), (VX["strand"], Y_STR),
      (X["aa"] - d, Y_STR), (X["aa"], Y_TRK)], C["strand"])
# FASTQ trunk
line([(X["inp"], Y_TRK), (X["end"], Y_TRK)], C["fastq"])
# SAM: input -> east -> up into first flagstat
line([(X["inp"], Y_LOW), (X["flag1"], Y_LOW), (X["flag1"], Y_TRK)], C["sam"])
# consensus: down from filter -> east
line([(X["filt"], Y_TRK), (X["filt"], Y_LOW), (X["aa"] + 10, Y_LOW)], C["consensus"])

# ---------------------------------------------------------------- stations
terminus(X["inp"], B["contam"], Y_TRK)
text(X["inp"], Y_TRK + 38, "FASTQ", 15, weight="bold")
text(X["inp"], Y_TRK + 55, "Illumina PE / SE", 12.5, fill="#555")
terminus(X["inp"], Y_LOW, Y_LOW)
text(X["inp"], Y_LOW + 38, "SAM", 15, weight="bold")
text(X["inp"], Y_LOW + 55, "aligned reads", 12.5, fill="#555")

for k, main, sub in [("fastqc", "FastQC", "raw reads"), ("fastp", "fastp", "trimming")]:
    pill(X[k], B["contam"], Y_TRK)
    label(X[k], Y_TRK, main, sub)

# contamination row
for x, m, s in [(560, "Kraken2", "classification"), (700, "Summary", "per sample"), (840, "Combine", "all samples")]:
    station(x, Y_CON); label(x, Y_CON, m, s, "above")
for x, m, s in [(560, "BBSplit", "vs subtype panel"), (700, "Estimate", "estimate_subtype.py"), (840, "Combine", "all samples")]:
    station(x, Y_SUB); label(x, Y_SUB, m, s, "above")
for x, m, s in [(X["bt2"], "Bowtie2", "PE, before merging"), (X["filt"], "samtools view", "filter"),
                (X["flag2"], "codonyat", "pre-merge pairs"), (X["cdy"], "Strand metrics", "strand_metrics.py")]:
    station(x, Y_STR); label(x, Y_STR, m, s, "above")

# trunk
trunk = [("bbmerge", "BBMerge", "PE only", "middle"), ("bt2", "Bowtie2", "merged + unmerged", "middle"),
         ("smerge", "samtools merge", "PE parts", "middle"), ("flag1", "flagstat", "aligned", "start"),
         ("filt", "Filter", "samtools view", "start"), ("flag2", "flagstat", "filtered", "middle"),
         ("cdy", "codonyat", "codon table", "middle"), ("aa", "Codon → AA", "codon_to_aa.py", "middle"),
         ("summ", "Summaries", "codonyat + AA", "middle")]
for k, m, s, anc in trunk:
    station(X[k], Y_TRK)
    lx = X[k] + 14 if anc == "start" else X[k]
    label(lx, Y_TRK, m, s, "below", anc)

# reporting
pill(X["mqc"], Y_CON, Y_TRK, 26)
text(X["mqc"] + 24, Y_TRK - 70, "MultiQC", 15, "start", "bold")
text(X["mqc"] + 24, Y_TRK - 53, "QC report", 12.5, "start", fill="#555")
station(X["prov"], Y_TRK)
label(X["prov"], Y_TRK, "Provenance", "versions · params · methods")
add(f'<circle cx="{X["end"]}" cy="{Y_TRK}" r="7" fill="#222"/>')

# consensus row
for x, m, s in [(X["flag2"], "samtools sort", ""), (X["cdy"], "iVar consensus", "IUPAC mixtures"),
                (X["aa"], "Consensus report", "FASTA + stats")]:
    station(x, Y_LOW); label(x, Y_LOW, m, s or None, "below")

# ---------------------------------------------------------------- legend
lx, ly = 40, 790
text(lx, ly - 14, "LEGEND", 12.5, "start", "bold", "#5a6675", 'letter-spacing="1.2"')
items = [("fastq", "FASTQ reads"), ("sam", "SAM input"), ("contam", "Contamination"),
         ("subtype", "Subtype estimate"), ("strand", "Strand branch"), ("consensus", "Consensus")]
for i, (k, name) in enumerate(items):
    x = lx + i * 190
    add(f'<line x1="{x}" y1="{ly + 6}" x2="{x + 44}" y2="{ly + 6}" stroke="{C[k]}" stroke-width="{LW}" stroke-linecap="round"/>')
    text(x + 54, ly + 11, name, 14, "start")
add(f'<circle cx="{lx + 1160}" cy="{ly + 6}" r="{R}" fill="#fff" stroke="#222" stroke-width="3"/>')
text(lx + 1180, ly + 11, "process", 14, "start")
add(f'<rect x="{lx + 1260}" y="{ly - 7}" width="16" height="26" rx="4" fill="#222"/>')
text(lx + 1286, ly + 11, "input", 14, "start")
text(lx, ly + 42, "SE reads, or --merge_pairs false: BBMerge and samtools merge are skipped and reads go straight to Bowtie2. "
     "SAM samples skip every FASTQ-only step.", 13, "start", fill="#444")
text(W - 20, H - 18, "nf-codonyat · research use only; no clinical or drug-resistance interpretation · github.com/sjoclaudi/nf-codonyat",
     12.5, "end", fill="#777")
add("</svg>")
open(sys.argv[1], "w").write("\n".join(out) + "\n")
