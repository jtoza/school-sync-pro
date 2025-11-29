def score_grade(score):
    """Return custom grade labels based on total score out of 100.
    Kenyan CBC grading: Exceeding, EE, ME, AE, BE.
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


def grade_to_points(grade):
    """Convert CBC grade to grade points for GPA calculation.
    Based on Kenyan CBC system.
    """
    grade_points = {
        "Exceeding": 4.0,
        "EE": 3.0,
        "ME": 2.0,
        "AE": 1.0,
        "BE": 0.0,
    }
    return grade_points.get(grade, 0.0)


def calculate_gpa(results):
    """
    Calculate GPA from a list of Result objects.
    Returns the average grade points.
    """
    if not results:
        return 0.0
    
    total_points = sum(grade_to_points(r.grade()) for r in results)
    return round(total_points / len(results), 2)


def get_gpa_class(gpa):
    """Return classification based on GPA."""
    if gpa >= 3.5:
        return "Excellent"
    elif gpa >= 3.0:
        return "Very Good"
    elif gpa >= 2.0:
        return "Good"
    elif gpa >= 1.0:
        return "Fair"
    else:
        return "Needs Improvement"


def calculate_class_rankings(student_class, session, term):
    """
    Calculate student rankings for a given class, session, and term.
    Returns a dictionary mapping student_id to position.
    """
    from apps.students.models import Student
    from .models import Result
    
    students = Student.objects.filter(current_class=student_class)
    rankings = []
    
    for student in students:
        results = Result.objects.filter(
            student=student,
            current_class=student_class,
            session=session,
            term=term
        )
        
        if results.exists():
            # Calculate average score
            total_score = sum(r.total_score() for r in results)
            avg_score = total_score / results.count()
            gpa = calculate_gpa(results)
            
            rankings.append({
                'student_id': student.id,
                'student': student,
                'avg_score': avg_score,
                'gpa': gpa,
                'total_score': total_score,
                'subject_count': results.count()
            })
    
    # Sort by average score (descending)
    rankings.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # Assign positions
    position_map = {}
    for idx, rank in enumerate(rankings, start=1):
        position_map[rank['student_id']] = {
            'position': idx,
            'avg_score': round(rank['avg_score'], 2),
            'gpa': rank['gpa'],
            'total_students': len(rankings)
        }
    
    return position_map


def get_student_position(student, session, term):
    """Get a student's position in their class for a given session and term."""
    if not student.current_class:
        return None
    
    rankings = calculate_class_rankings(student.current_class, session, term)
    return rankings.get(student.id)


def get_performance_trend(student, subject=None):
    """
    Get performance trend over time for a student.
    Returns list of sessions/terms with scores.
    """
    from .models import Result
    
    if subject:
        results = Result.objects.filter(
            student=student,
            subject=subject
        ).order_by('session__name', 'term__name')
    else:
        results = Result.objects.filter(
            student=student
        ).order_by('session__name', 'term__name')
    
    trend = []
    current_key = None
    current_scores = []
    
    for result in results:
        key = f"{result.session.name} - {result.term.name}"
        if key != current_key:
            if current_scores:
                avg = sum(current_scores) / len(current_scores)
                trend.append({
                    'period': current_key,
                    'average': round(avg, 2),
                    'count': len(current_scores)
                })
            current_key = key
            current_scores = [result.total_score()]
        else:
            current_scores.append(result.total_score())
    
    # Add the last period
    if current_scores:
        avg = sum(current_scores) / len(current_scores)
        trend.append({
            'period': current_key,
            'average': round(avg, 2),
            'count': len(current_scores)
        })
    
    return trend


def get_subject_analytics(student_class, session, term, subject):
    """Get analytics for a specific subject in a class."""
    from .models import Result
    
    results = Result.objects.filter(
        current_class=student_class,
        session=session,
        term=term,
        subject=subject
    )
    
    if not results.exists():
        return None
    
    scores = [r.total_score() for r in results]
    
    return {
        'subject': subject.name,
        'average': round(sum(scores) / len(scores), 2),
        'highest': max(scores),
        'lowest': min(scores),
        'total_students': len(scores),
        'passing': sum(1 for s in scores if s >= 50),  # 50% pass mark
        'pass_rate': round((sum(1 for s in scores if s >= 50) / len(scores)) * 100, 2)
    }
