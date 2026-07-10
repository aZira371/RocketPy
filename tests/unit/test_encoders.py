"""Unit tests for the RocketPy JSON encoder/decoder helpers."""

import importlib
import json
import warnings

import pytest

from rocketpy._encoders import RocketPyDecoder, get_class_from_signature
from rocketpy.rocket.parachutes import HemisphericalParachute, Parachute


def test_get_class_from_signature_remaps_legacy_parachute():
    """The legacy ``rocketpy.rocket.parachute.Parachute`` signature must remap to
    ``Parachute`` in its new location (the old module was moved to the
    ``rocketpy.rocket.parachutes`` subpackage)."""
    legacy_signature = {
        "module": "rocketpy.rocket.parachute",
        "name": "Parachute",
    }
    assert get_class_from_signature(legacy_signature) is Parachute


def test_decode_legacy_parachute_rpy_reconstructs_object():
    """Regression: parachutes saved in ``.rpy`` files by older versions used the
    now-deleted ``rocketpy.rocket.parachute`` module path. They must still
    reconstruct as a concrete parachute object instead of silently returning a
    raw dict."""
    legacy_entry = {
        "signature": {"module": "rocketpy.rocket.parachute", "name": "Parachute"},
        "name": "drogue",
        "cd_s": 1.0,
        "trigger": "apogee",
        "sampling_rate": 105,
        "lag": 1.5,
        "noise": [0, 8.3, 0.5],
        "radius": 0.5,
        "drag_coefficient": 1.4,
        "height": 0.5,
        "porosity": 0.0432,
    }

    decoded = json.loads(json.dumps(legacy_entry), cls=RocketPyDecoder)

    assert isinstance(decoded, Parachute)
    assert decoded.name == "drogue"
    assert decoded.cd_s == 1.0
    assert decoded.lag == 1.5
    assert decoded.noise_deviation == 8.3
    assert callable(decoded.triggerfunc)


def test_decoder_warns_on_unresolvable_signature():
    """An unresolvable signature must surface a warning rather than silently
    returning a raw dictionary (which previously masked data loss)."""
    entry = {
        "signature": {"module": "rocketpy.does_not_exist", "name": "Ghost"},
        "value": 1,
    }
    with pytest.warns(UserWarning, match="Could not reconstruct"):
        decoded = json.loads(json.dumps(entry), cls=RocketPyDecoder)
    assert decoded == {"value": 1}


def test_legacy_parachute_module_import_is_deprecated():
    """Importing from the old ``rocketpy.rocket.parachute`` module path must
    still work but emit a ``DeprecationWarning``."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with pytest.raises(DeprecationWarning):
            importlib.reload(importlib.import_module("rocketpy.rocket.parachute"))

    module = importlib.import_module("rocketpy.rocket.parachute")
    assert module.Parachute is Parachute
    assert module.HemisphericalParachute is HemisphericalParachute
