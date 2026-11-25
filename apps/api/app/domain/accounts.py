"""Pure rules for accounts (US-01)."""

from datetime import date

ADULT_AGE = 18


def age_on(birth_date: date, today: date) -> int:
    """Full years on `today`. Someone born on 29 Feb turns a year older on 1 Mar in non-leap years."""
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def old_enough(birth_date: date, today: date) -> bool:
    """BR-01, NEVER-04: 17 years 364 days is not enough; the 18th birthday itself is."""
    return age_on(birth_date, today) >= ADULT_AGE
