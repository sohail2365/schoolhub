from datetime import date
from utils.validators import validate_minimum_age


def test_minimum_age_validation():
    assert validate_minimum_age(date(2010, 1, 1), 3) is True
