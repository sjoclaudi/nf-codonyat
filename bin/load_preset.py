#!/usr/bin/env python3
"""Load nf-codonyat preset configuration.

Usage:
    load_preset.py --preset hiv1 --project-dir /path/to/nf-codonyat

Outputs JSON with resolved paths and config:
{
    "reference": "/path/to/preset/reference.fasta",
    "amplicons": "/path/to/preset/amplicons.tsv",  # or null
    "primer_bed": "/path/to/preset/primers.bed",   # or null
    "subtype_panel": "/path/to/preset/subtype_panel",  # or null
    "target_taxid": 11676,
    "target_label": "HIV1",
    "reference_accessions": ["K03455.1"]
}
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # Minimal YAML parser for simple key: value files
    class yaml:
        @staticmethod
        def safe_load(f):
            result = {}
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip()
                    # Try to parse as int
                    try:
                        value = int(value)
                    except ValueError:
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                    result[key] = value
            return result


def load_preset(preset_name: str, project_dir: Path) -> dict:
    """Load preset configuration and return resolved paths."""
    preset_dir = project_dir / "assets" / "presets" / preset_name
    
    if not preset_dir.exists():
        print(f"Error: Preset '{preset_name}' not found at {preset_dir}", file=sys.stderr)
        sys.exit(1)
    
    preset_yml = preset_dir / "preset.yml"
    if not preset_yml.exists():
        print(f"Error: {preset_yml} not found", file=sys.stderr)
        sys.exit(1)
    
    # Load preset.yml
    with open(preset_yml) as f:
        config = yaml.safe_load(f)
    
    # Build result with resolved paths
    result = {
        "target_taxid": config.get("target_taxid"),
        "target_label": config.get("target_label", "TARGET"),
        "reference_accessions": [config.get("reference_accession")] if config.get("reference_accession") else []
    }
    
    # Check for reference
    ref_path = preset_dir / "reference.fasta"
    if ref_path.exists():
        result["reference"] = str(ref_path)
    else:
        result["reference"] = None
    
    # Check for amplicons (HIV-1 keeps this format)
    amp_path = preset_dir / "amplicons.tsv"
    if amp_path.exists():
        result["amplicons"] = str(amp_path)
        result["primer_bed"] = None
    else:
        result["amplicons"] = None
        # Check for primers.bed (other presets)
        bed_path = preset_dir / "primers.bed"
        if bed_path.exists():
            result["primer_bed"] = str(bed_path)
        else:
            result["primer_bed"] = None
    
    # Check for subtype panel
    panel_dir = preset_dir / "subtype_panel"
    if panel_dir.exists() and panel_dir.is_dir():
        result["subtype_panel"] = str(panel_dir)
    else:
        result["subtype_panel"] = None
    
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, 
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preset", required=True, help="Preset name")
    parser.add_argument("--project-dir", required=True, type=Path, help="Project directory")
    
    args = parser.parse_args()
    
    result = load_preset(args.preset, args.project_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
