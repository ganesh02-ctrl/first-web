from decimal import Decimal
from types import SimpleNamespace as NS

from app.utils.gpa import calculate_cgpa, calculate_sgpa


def s(c, gp, counts=True):
    return NS(credits=Decimal(str(c)), grade_point=Decimal(str(gp)), counts_in_gpa=counts)


def test_sgpa_weighted():
    assert calculate_sgpa([s(4, 10), s(3, 8), s(1, 6)]).gpa == Decimal("8.75")  # 70/8


def test_cgpa_is_not_average_of_sgpa():
    sem1 = NS(subjects=[s(4, 10)])          # SGPA 10
    sem2 = NS(subjects=[s(20, 6)])          # SGPA 6
    assert calculate_cgpa([sem1, sem2]).gpa == Decimal("6.67")  # 160/24, not 8.0


def test_excluded_and_empty():
    assert calculate_sgpa([s(2, 0, counts=False), s(4, 9)]).gpa == Decimal("9.00")
    assert calculate_sgpa([]).gpa is None
