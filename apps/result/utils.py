def score_grade(score):
    """Return custom grade labels based on total score out of 100.
    Bands provided by user: Exceeding, EE, ME, AE, BE mapping to A-E.
    """
    try:
        s = float(score)
    except Exception:
        return ""
    if s >= 80:
        return "Exceeding"
    if 70 <= s < 80:
        return "EE"
    if 60 <= s < 70:
        return "ME"
    if 50 <= s < 60:
        return "AE"
    return "BE"
