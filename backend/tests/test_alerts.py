from backend.services.alert_service import build_alert, classify_reading


def test_classify_reading_returns_not_charging_when_below_min():
    assert classify_reading(10, 50, 500) == "not_charging"


def test_classify_reading_returns_charging_when_inside_range():
    assert classify_reading(120, 50, 500) == "charging"


def test_classify_reading_returns_abnormal_when_above_max():
    assert classify_reading(600, 50, 500) == "abnormal"


def test_build_alert_returns_payload_for_low_current():
    alert = build_alert(10, 50, 500)
    assert alert["type"] == "low_current"


def test_build_alert_returns_none_when_value_is_normal():
    assert build_alert(120, 50, 500) is None
