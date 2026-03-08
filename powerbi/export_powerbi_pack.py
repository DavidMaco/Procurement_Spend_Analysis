from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from dashboard_data import (
    RAW_DATASETS,
    build_bundle_from_uploaded_frames,
    export_powerbi_pack,
    generate_demo_bundle,
    load_demo_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Power BI deployment pack.")
    parser.add_argument("--mode", choices=["demo", "generate", "folder"], default="demo")
    parser.add_argument("--output", default="procurement_powerbi_pack.zip")
    parser.add_argument("--input-dir", help="Folder containing external company CSV extracts.")
    parser.add_argument("--num-orders", type=int, default=2500)
    parser.add_argument("--quality-incidents", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _load_folder_tables(input_dir: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for dataset_key, filename in RAW_DATASETS.items():
        file_path = input_dir / filename
        if file_path.exists():
            frames[dataset_key] = pd.read_csv(file_path)
    if not frames:
        raise FileNotFoundError(f"No canonical CSV files found in {input_dir}")
    return frames


def main() -> None:
    args = parse_args()

    if args.mode == "demo":
        bundle = load_demo_bundle()
    elif args.mode == "generate":
        bundle = generate_demo_bundle(
            num_orders=args.num_orders,
            num_quality_incidents=args.quality_incidents,
            seed=args.seed,
        )
    else:
        if not args.input_dir:
            raise ValueError("--input-dir is required when --mode folder")
        frames = _load_folder_tables(Path(args.input_dir))
        bundle = build_bundle_from_uploaded_frames(frames, source_label="Folder-based company data")

    payload = export_powerbi_pack(bundle)
    output_path = Path(args.output)
    output_path.write_bytes(payload)
    print(f"Power BI deployment pack written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
