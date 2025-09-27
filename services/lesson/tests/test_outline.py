import pytest
from services.lesson.outline import outline_steps

def test_outline_steps_default():
    """Tests the default lesson pattern with no special features."""
    features = {}
    expected = ["read", "check", "explain", "check", "reflect"]
    result = outline_steps(features)
    assert result == expected

def test_outline_steps_with_media():
    """Tests that a 'spot' step is added when 'has_media' is true."""
    features = {"has_media": True}
    expected = ["read", "spot", "check", "explain", "check", "reflect"]
    result = outline_steps(features)
    assert result == expected

def test_outline_steps_with_multiple_claims():
    """Tests that an extra 'check' step is added when there are multiple claims."""
    features = {"claims_count": 2}
    expected = ["read", "check", "explain", "check", "check", "reflect"]
    result = outline_steps(features)
    assert result == expected

def test_outline_steps_with_single_claim():
    """Tests that no extra 'check' is added for a single claim."""
    features = {"claims_count": 1}
    expected = ["read", "check", "explain", "check", "reflect"]
    result = outline_steps(features)
    assert result == expected

def test_outline_steps_with_media_and_multiple_claims():
    """Tests the case where both media and multiple claims are present."""
    features = {"has_media": True, "claims_count": 3}
    expected = ["read", "spot", "check", "explain", "check", "check", "reflect"]
    result = outline_steps(features)
    assert result == expected

def test_first_and_last_steps_are_constant():
    """Ensures that 'read' is always the first step and 'reflect' is always the last."""
    # Test with no features
    steps_default = outline_steps({})
    assert steps_default[0] == "read"
    assert steps_default[-1] == "reflect"

    # Test with all features
    steps_full = outline_steps({"has_media": True, "claims_count": 5})
    assert steps_full[0] == "read"
    assert steps_full[-1] == "reflect"