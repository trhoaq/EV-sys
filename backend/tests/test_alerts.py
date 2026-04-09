from backend.services.alert_service import build_alert, classify_reading, detect_statistical_current_anomaly


def test_classify_reading_returns_not_charging_when_below_min():
    assert classify_reading(10, 50, 500) == "not_charging"


def test_classify_reading_returns_charging_when_inside_range():
    assert classify_reading(120, 50, 500) == "charging"


def test_classify_reading_returns_abnormal_when_above_max():
    assert classify_reading(600, 50, 500) == "abnormal"


def test_build_alert_returns_none_for_low_current():
    assert build_alert(10, 50, 500) is None


def test_build_alert_returns_none_when_value_is_normal():
    assert build_alert(120, 50, 500) is None


def test_detect_statistical_current_anomaly_returns_none_for_small_sample():
    result = detect_statistical_current_anomaly(
        current=150,
        history=[118, 121, 119],
        min_samples=5,
        z_threshold=3.5,
        relative_delta_threshold=0.25,
    )

    assert result is None


def test_detect_statistical_current_anomaly_flags_robust_outlier():
    result = detect_statistical_current_anomaly(
        current=190,
        history=[118, 121, 119, 120, 122, 117, 118, 121],
        min_samples=5,
        z_threshold=3.5,
        relative_delta_threshold=0.25,
    )

    assert result is not None
    assert result["basis"] == "robust_z_score"
