from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction

import pytest

from bridge import ProbabilityValue


def test_probability_value_normalizes_to_reduced_fraction() -> None:
    assert ProbabilityValue(2, 4) == ProbabilityValue(1, 2)
    assert ProbabilityValue(2, 4).to_canonical_dict() == {
        "numerator": 1,
        "denominator": 2,
    }


@pytest.mark.parametrize(
    ("numerator", "denominator", "message"),
    (
        (-1, 2, "closed interval"),
        (3, 2, "closed interval"),
        (1, 0, "positive"),
        (1, -2, "positive"),
    ),
)
def test_probability_value_rejects_invalid_bounds(
    numerator: int,
    denominator: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ProbabilityValue(numerator, denominator)


@pytest.mark.parametrize(
    ("numerator", "denominator"),
    (
        (0.5, 1),
        (1, 2.0),
        (True, 1),
        (1, False),
        ("1", 2),
        (1, "2"),
        (Decimal("0.5"), 1),
        (1, Decimal("2")),
        (Fraction(1, 2), 1),
        (1, object()),
    ),
)
def test_probability_value_rejects_noninteger_components(
    numerator: object,
    denominator: object,
) -> None:
    with pytest.raises(TypeError, match="integers"):
        ProbabilityValue(numerator, denominator)  # type: ignore[arg-type]


def test_probability_value_exact_zero_and_one() -> None:
    zero = ProbabilityValue(0, 9)
    one = ProbabilityValue(9, 9)
    assert zero == ProbabilityValue(0, 1) and zero.is_zero and not zero.is_one
    assert one == ProbabilityValue(1, 1) and one.is_one and not one.is_zero


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (ProbabilityValue(1, 4), ProbabilityValue(3, 4)),
        (ProbabilityValue(0, 1), ProbabilityValue(1, 1)),
        (ProbabilityValue(1, 1), ProbabilityValue(0, 1)),
    ),
)
def test_probability_value_complement_is_exact(
    value: ProbabilityValue,
    expected: ProbabilityValue,
) -> None:
    complement = value.complement()
    assert complement == expected
    assert value.as_fraction() + complement.as_fraction() == Fraction(1, 1)


def test_probability_value_ordering_is_exact_and_deterministic() -> None:
    assert ProbabilityValue(1, 3) < ProbabilityValue(1, 2) < ProbabilityValue(2, 3)
    assert ProbabilityValue(0, 1) < ProbabilityValue(1, 999_999)
    assert ProbabilityValue(999_999, 1_000_000) < ProbabilityValue(1, 1)


def test_probability_value_comparisons_do_not_coerce_other_types() -> None:
    value = ProbabilityValue(1, 2)
    assert value != 0.5
    assert value != Fraction(1, 2)
    assert value != Decimal("0.5")
    assert value != (1, 2)
    assert value != {"numerator": 1, "denominator": 2}
    with pytest.raises(TypeError):
        value < Fraction(2, 3)  # type: ignore[operator]


def test_probability_value_large_integers_remain_exact() -> None:
    factor = 10**100
    value = ProbabilityValue(2 * factor, 4 * factor)
    assert value == ProbabilityValue(1, 2)
    assert value.complement() == ProbabilityValue(1, 2)


def test_probability_value_serialization_round_trip_is_exact() -> None:
    original = ProbabilityValue.from_fraction(22, 29)
    payload = original.to_canonical_dict()
    second_payload = original.to_canonical_dict()
    assert payload == {"numerator": 22, "denominator": 29}
    assert payload is not second_payload
    payload["numerator"] = 1
    assert original == ProbabilityValue(22, 29)
    assert ProbabilityValue.from_canonical_dict(second_payload) == original


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"numerator": 1},
        {"numerator": 1, "denominator": 2, "display": "50%"},
        {"numerator": True, "denominator": 2},
        {"numerator": 1, "denominator": False},
        {"numerator": 0.5, "denominator": 1},
        {"numerator": "1", "denominator": 2},
        {"numerator": -1, "denominator": 2},
        {"numerator": 1, "denominator": 0},
        {"numerator": 1, "denominator": -2},
        {"numerator": 3, "denominator": 2},
    ),
)
def test_probability_value_rejects_noncanonical_payload(payload: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        ProbabilityValue.from_canonical_dict(payload)  # type: ignore[arg-type]


def test_probability_value_is_immutable_and_hashable() -> None:
    value = ProbabilityValue(1, 2)
    assert {value, ProbabilityValue(2, 4)} == {value}
    with pytest.raises(FrozenInstanceError):
        value.numerator = 2  # type: ignore[misc]


def test_probability_value_has_no_approximate_or_implicit_display_api() -> None:
    public_names = {name for name, _ in inspect.getmembers(ProbabilityValue)}
    assert "from_float" not in public_names
    assert "__float__" not in public_names
    assert "isclose" not in public_names
    assert "to_percentage" not in public_names
    assert "to_decimal_string" not in public_names


def test_probability_value_is_formula_and_bridge_semantics_neutral() -> None:
    fields = set(ProbabilityValue.__dataclass_fields__)
    assert fields == {"numerator", "denominator"}
    assert not fields.intersection(
        {"restricted_choice", "vacant_places", "card", "seat", "recommendation"}
    )
