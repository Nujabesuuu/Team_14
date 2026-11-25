"""US-01, BR-01: who may register. Boundaries from the Scenario Outline «Межа віку 18 років»."""

from datetime import date

import pytest

from app.domain.accounts import age_on, old_enough

TODAY = date(2026, 11, 20)


@pytest.mark.parametrize(
    "birth_date,expected",
    [
        (date(2001, 11, 20), True),  # 25 years
        (date(2008, 11, 20), True),  # exactly 18: the birthday itself counts
        (date(2008, 11, 21), False),  # 17 years 364 days
        (date(2010, 11, 20), False),  # 16 years
    ],
    ids=["25 years", "exactly 18", "17 years 364 days", "16 years"],
)
def test_old_enough_on_the_day_of_registration(birth_date, expected):
    assert old_enough(birth_date, TODAY) is expected


def test_born_on_29_february_turns_18_on_1_march_in_a_common_year():
    assert age_on(date(2008, 2, 29), date(2026, 2, 28)) == 17
    assert age_on(date(2008, 2, 29), date(2026, 3, 1)) == 18
