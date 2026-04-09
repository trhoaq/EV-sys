from __future__ import annotations

from datetime import timezone

from backend.extensions import db
from backend.models.entities import ChargingSession


def get_active_session(device_id: int) -> ChargingSession | None:
    return (
        ChargingSession.query.filter_by(device_id=device_id, status="active")
        .order_by(ChargingSession.started_at.desc())
        .first()
    )


def start_session(
    *,
    device_id: int,
    vehicle_id: int,
    started_at,
    power_w: float,
    rate_vnd_per_kwh: int,
) -> ChargingSession:
    session = ChargingSession(
        device_id=device_id,
        vehicle_id=vehicle_id,
        status="active",
        started_at=started_at,
        last_sample_at=started_at,
        last_power_w=power_w,
        reading_count=1,
        energy_kwh=0.0,
        rate_vnd_per_kwh=rate_vnd_per_kwh,
        total_vnd=0,
    )
    db.session.add(session)
    db.session.flush()
    return session


def update_session_sample(session: ChargingSession, *, sample_at, power_w: float) -> None:
    previous_sample_at = _normalize_utc(session.last_sample_at)
    current_sample_at = _normalize_utc(sample_at)
    delta_seconds = max((current_sample_at - previous_sample_at).total_seconds(), 0.0)

    if delta_seconds > 0:
        average_power_w = max((session.last_power_w + power_w) / 2.0, 0.0)
        session.energy_kwh += average_power_w * (delta_seconds / 3600.0) / 1000.0

    session.last_sample_at = sample_at
    session.last_power_w = power_w
    session.reading_count += 1


def close_session(session: ChargingSession, *, ended_at, final_power_w: float = 0.0) -> None:
    update_session_sample(session, sample_at=ended_at, power_w=final_power_w)
    session.ended_at = ended_at
    session.status = "completed"
    session.total_vnd = int(round(session.energy_kwh * session.rate_vnd_per_kwh))


def _normalize_utc(value):
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
