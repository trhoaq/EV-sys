from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from backend import create_app
from backend.extensions import db
from backend.services.alert_service import upsert_system_settings
from backend.services.fake_db_seed_service import build_fake_payloads, load_fake_payloads_to_db


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate fake charging payloads and insert them into the database.")
    parser.add_argument("--device-code", default="esp32s3_01")
    parser.add_argument("--license-plate", default="59A-12345")
    parser.add_argument("--duration-minutes", type=int, default=120)
    parser.add_argument("--current-min-a", type=float, default=9.0)
    parser.add_argument("--current-max-a", type=float, default=12.0)
    parser.add_argument("--voltage-min-v", type=float, default=23.0)
    parser.add_argument("--voltage-max-v", type=float, default=25.5)
    parser.add_argument("--seed", type=int, default=20260410)
    parser.add_argument("--anomaly-minutes", default="32,79,104")
    parser.add_argument("--single-device", action="store_true")
    parser.add_argument("--no-preview-file", action="store_true")
    parser.add_argument("--keep-settings", action="store_true")
    return parser


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(repo_root / ".env")
    parser = build_parser()
    args = parser.parse_args()

    anomaly_minutes = [
        int(value.strip())
        for value in args.anomaly_minutes.split(",")
        if value.strip()
    ]

    app = create_app()
    with app.app_context():
        db.create_all()
        if not args.keep_settings:
            upsert_system_settings(
                min_current_ma=max(1.0, args.current_min_a - 1.0),
                max_current_ma=args.current_max_a + 6.0,
                updated_by=None,
                charging_detection_current_ma=max(0.5, args.current_min_a - 0.5),
            )
        payloads = build_fake_payloads(
            single_device=args.single_device,
            device_code=args.device_code,
            license_plate=args.license_plate,
            duration_minutes=args.duration_minutes,
            current_min_a=args.current_min_a,
            current_max_a=args.current_max_a,
            voltage_min_v=args.voltage_min_v,
            voltage_max_v=args.voltage_max_v,
            anomaly_minutes=anomaly_minutes,
            seed=args.seed,
        )
        summary = load_fake_payloads_to_db(
            payloads=payloads,
            preview_path=app.config["FAKE_PAYLOADS_PREVIEW_PATH"],
            write_preview_file=not args.no_preview_file,
        )

    print("Loaded fake payloads into database.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
