def calculate_percentage(marks_obtained: float, total_marks: float) -> float:
    return round((marks_obtained / total_marks) * 100, 2)


def get_grade_letter(percentage: float) -> str:
    if percentage >= 80:
        return "A"
    if percentage >= 60:
        return "B"
    if percentage >= 40:
        return "C"
    if percentage >= 25:
        return "D"
    return "F"
