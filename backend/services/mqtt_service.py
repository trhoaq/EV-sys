from __future__ import annotations

import json
from typing import Any

import paho.mqtt.client as mqtt
from flask import Flask

from backend.services.ingest_service import ingest_sensor_payload as ingest_sensor_payload_internal

_mqtt_app: Flask | None = None
_mqtt_client: mqtt.Client | None = None


def init_mqtt(app: Flask) -> None:
    global _mqtt_app, _mqtt_client

    if app.config["TESTING"] or not app.config["MQTT_ENABLED"] or _mqtt_client is not None:
        return

    _mqtt_app = app
    client = mqtt.Client(client_id=app.config["MQTT_CLIENT_ID"])

    if app.config["MQTT_USERNAME"]:
        client.username_pw_set(app.config["MQTT_USERNAME"], app.config["MQTT_PASSWORD"])

    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(app.config["MQTT_HOST"], app.config["MQTT_PORT"], keepalive=60)
        client.loop_start()
        _mqtt_client = client
    except Exception as exc:
        app.logger.warning("MQTT init failed: %s", exc)


def _on_connect(client: mqtt.Client, _userdata: Any, _flags: dict, reason_code: int, _properties=None) -> None:
    if reason_code == 0 and _mqtt_app is not None:
        client.subscribe(_mqtt_app.config["MQTT_SENSOR_TOPIC"])


def _on_message(_client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
    if _mqtt_app is None:
        return

    payload = json.loads(message.payload.decode("utf-8"))
    with _mqtt_app.app_context():
        ingest_sensor_payload_internal(payload)


def ingest_sensor_payload(payload: dict, app: Flask | None = None) -> dict:
    if app is not None:
        with app.app_context():
            result = ingest_sensor_payload_internal(payload)
    else:
        result = ingest_sensor_payload_internal(payload)

    return {
        "sensor_data_id": result["reading"]["id"],
        "device": result["device"],
        "vehicle": result["vehicle"],
        "alert": result["alert"],
    }
