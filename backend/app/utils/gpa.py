"""Credit-weighted SGPA / CGPA calculation (pure functions, no DB access).

SGPA = Σ(credit × grade point) / Σ(credits)            for one semester
CGPA = Σ(credit × grade point) / Σ(credits)            across ALL semesters' subjects
(CGPA is NOT the plain average of SGPAs.)

Subjects whose grade is marked counts_in_gpa=False (e.g. audit / non-credit courses)
are excluded from both numerator and denominator.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class GradedItem:
    credits: Decimal
    grade_point: Decimal
    counts_in_gpa: bool = True


@dataclass(frozen=True)
class GpaResult:
    gpa: Decimal | None
    total_credits: Decimal
    total_points: Decimal

    def as_dict(self) -> dict:
        return {
            "gpa": float(self.gpa) if self.gpa is not None else None,
            "total_credits": float(self.total_credits),
            "total_points": float(self.total_points),
        }


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def weighted_gpa(items: Iterable[GradedItem]) -> GpaResult:
    total_credits = Decimal("0")
    total_points = Decimal("0")
    for item in items:
        if not item.counts_in_gpa:
            continue
        credits = _to_decimal(item.credits)
        if credits <= 0:
            continue
        total_credits += credits
        total_points += credits * _to_decimal(item.grade_point)
    if total_credits == 0:
        return GpaResult(None, total_credits, total_points)
    gpa = (total_points / total_credits).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    return GpaResult(gpa, total_credits, total_points)


def calculate_sgpa(subjects: Iterable) -> GpaResult:
    """Accepts any objects exposing credits, grade_point and counts_in_gpa."""
    return weighted_gpa(
        GradedItem(_to_decimal(s.credits), _to_decimal(s.grade_point), bool(getattr(s, "counts_in_gpa", True)))
        for s in subjects
    )


def calculate_cgpa(semesters: Iterable) -> GpaResult:
    """Accepts objects exposing .subjects; weights every subject across all semesters."""
    def all_subjects():
        for semester in semesters:
            yield from semester.subjects
    return calculate_sgpa(all_subjects())
