import pytest

from bender.parameter import (
    BoolParameter,
    FloatParameter,
    IntParameter,
    StringParameter,
    build_parameters,
)


def test_string_parameter():
    param = StringParameter(description="Test String")
    assert param.parse("Some string") == "Some string"


def test_bool_parameter():
    param = BoolParameter(description="Test Boolean")

    assert param.parse("true") is True
    assert param.parse("false") is False
    assert param.parse("yes") is True
    assert param.parse("no") is False
    assert param.parse("1") is True
    assert param.parse("0") is False

    with pytest.raises(ValueError):
        param.parse("not a boolean")


def test_int_parameter():
    param = IntParameter(description="Test Int", min_value=0, max_value=10)

    assert param.parse("5") == 5

    with pytest.raises(ValueError):
        param.parse("15")

    # Test clamping
    param_clamp = IntParameter(
        description="Test Int", min_value=0, max_value=10, clamp=True
    )
    assert param_clamp.parse("15") == 10
    assert param_clamp.parse("-5") == 0


def test_float_parameter():
    param = FloatParameter(description="Test Float", min_value=0.5, max_value=3.5)

    assert param.parse("2.5") == 2.5

    with pytest.raises(ValueError):
        param.parse("4.0")

    # Test clamping
    param_clamp = FloatParameter(
        description="Test Float", min_value=0.5, max_value=3.5, clamp=True
    )
    assert param_clamp.parse("4.0") == 3.5
    assert param_clamp.parse("0.1") == 0.5


def test_build_parameters():
    prototypes = {
        "param1": StringParameter(description="Param 1"),
        "param2": BoolParameter(description="Param 2", required=True),
        "param3": IntParameter(description="Param 3", default=10),
        "param4": FloatParameter(
            description="Param 4", min_value=1.0, max_value=10.0, required=True
        ),
    }

    values = {"param1": "value1", "param2": "true", "param4": "5.5"}
    parsed_parameters = build_parameters(prototypes, values)

    assert parsed_parameters == {
        "param1": "value1",
        "param2": True,
        "param3": 10,
        "param4": 5.5,
    }

    # Test required parameter missing
    incomplete_values = {"param1": "value1", "param4": "5.5"}
    with pytest.raises(ValueError):
        build_parameters(prototypes, incomplete_values)

    # Test unknown parameter
    unknown_values = {"param1": "value1", "param2": "true", "unknown": "something"}
    with pytest.raises(ValueError):
        build_parameters(prototypes, unknown_values)
