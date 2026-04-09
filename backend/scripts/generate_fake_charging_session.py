from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from backend.services.fake_session_service import (
    generate_fake_charging_session,
    generate_fake_payload_fleet,
    resolve_seed,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or publish fake 2-hour charging telemetry.")
    parser.add_argument("--device-code", default="esp32s3_01")
    parser.add_argument("--license-plate", default="59A-12345")
    parser.add_argument("--duration-minutes", type=int, default=120)
    parser.add_argument("--current-min-a", type=float, default=9.0)
    parser.add_argument("--current-max-a", type=float, default=12.0)
    parser.add_argument("--voltage-min-v", type=float, default=23.0)
    parser.add_argument("--voltage-max-v", type=float, default=25.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--anomaly-minutes", default="32,79,104")
    parser.add_argument("--single-device", action="store_true")
    parser.add_argument("--output", default="backend\\samples\\fake_payloads_latest.jsonl")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--topic", default=None)
    parser.add_argument("--mqtt-host", default=None)
    parser.add_argument("--mqtt-port", type=int, default=None)
    parser.add_argument("--mqtt-username", default=None)
    parser.add_argument("--mqtt-password", default=None)
    parser.add_argument("--delay-seconds", type=float, default=0.05)
    return parser


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    parser = build_parser()
    args = parser.parse_args()

    anomaly_minutes = [
        int(value.strip())
        for value in args.anomaly_minutes.split(",")
        if value.strip()
    ]
    seed_used = resolve_seed(args.seed)

    if args.single_device:
        payloads = generate_fake_charging_session(
            device_code=args.device_code,
            license_plate=args.license_plate,
            duration_minutes=args.duration_minutes,
            current_min_a=args.current_min_a,
            current_max_a=args.current_max_a,
            voltage_min_v=args.voltage_min_v,
            voltage_max_v=args.voltage_max_v,
            anomaly_minutes=anomaly_minutes,
            seed=seed_used,
        )
    else:
        payloads = generate_fake_payload_fleet(
            duration_minutes=args.duration_minutes,
            current_min_a=args.current_min_a,
            current_max_a=args.current_max_a,
            voltage_min_v=args.voltage_min_v,
            voltage_max_v=args.voltage_max_v,
            seed=seed_used,
        )

    if args.publish:
        _publish_payloads(args, payloads, seed_used)
    else:
        _write_payloads(args, payloads, seed_used)


def _write_payloads(args, payloads: list[dict], seed_used: int) -> None:
    lines = [json.dumps(payload, ensure_ascii=True) for payload in payloads]
    if args.stdout:
        print(f"# seed_used={seed_used}")
        print("\n".join(lines))
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(payloads)} fake telemetry rows to {output_path}")
    print(f"seed_used: {seed_used}")


def _publish_payloads(args, payloads: list[dict], seed_used: int) -> None:
    topic = args.topic or _read_env("MQTT_SENSOR_TOPIC", "ina219/data")
    host = args.mqtt_host or _read_env("MQTT_HOST", "127.0.0.1")
    port = args.mqtt_port or int(_read_env("MQTT_PORT", "1883"))
    username = args.mqtt_username or _read_env("MQTT_USERNAME", "")
    password = args.mqtt_password or _read_env("MQTT_PASSWORD", "")

    client = mqtt.Client(client_id=f"{args.device_code}_fake_session")
    if username:
        client.username_pw_set(username, password)

    client.connect(host, port, keepalive=60)
    client.loop_start()
    try:
        for payload in payloads:
            client.publish(topic, json.dumps(payload, ensure_ascii=True))
            time.sleep(args.delay_seconds)
    finally:
        client.loop_stop()
        client.disconnect()

    print(f"Published {len(payloads)} fake telemetry rows to {topic} on {host}:{port}")
    print(f"seed_used: {seed_used}")


def _read_env(name: str, default: str) -> str:
    from os import getenv

    return getenv(name, default)


if __name__ == "__main__":
    main()
