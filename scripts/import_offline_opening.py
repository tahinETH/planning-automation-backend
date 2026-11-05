#!/usr/bin/env python3
"""Create a new target from an approved offline export. Never switch a service."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.handover import import_offline_opening


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--area', choices=['torna', 'cubuk-filtre'], required=True)
    parser.add_argument('--generation', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--source-uploads', type=Path)
    parser.add_argument('--target-uploads', type=Path)
    args = parser.parse_args()
    receipt = import_offline_opening(args.source, args.target, area=args.area, generation_id=args.generation,
                                     expected_sha256=args.source_sha256, source_upload_dir=args.source_uploads,
                                     target_upload_dir=args.target_uploads)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
