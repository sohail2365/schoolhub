from utils.helpers import calculate_percentage, get_grade_letter


def test_percentage_and_letter():
    pct = calculate_percentage(40, 50)
    assert pct == 80.0
    assert get_grade_letter(pct) == "A"
    assert get_grade_letter(60) == "B"
    assert get_grade_letter(40) == "C"
    assert get_grade_letter(25) == "D"
    assert get_grade_letter(24.99) == "F"
