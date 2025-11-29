"""
Additional views for enhanced results features.
This file contains analytics dashboard and bulk upload functionality.
"""

import json
import csv
from io import TextIOWrapper
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Avg, Count, F, FloatField, ExpressionWrapper
from apps.corecode.models import StudentClass, Subject, AcademicSession, AcademicTerm
from apps.students.models import Student
from .models import Result
from .forms import BulkUploadForm
from .utils import (
    calculate_gpa, get_gpa_class, calculate_class_rankings,
    get_performance_trend, get_subject_analytics
)


@login_required
def analytics_dashboard(request):
    """
    Beautiful analytics dashboard with charts and insights.
    Shows GPA, rankings, performance trends, and subject analytics.
    """
    session = request.current_session
    term = request.current_term
    selected_class_id = request.GET.get('class')
    
    # Get all classes for dropdown
    classes = StudentClass.objects.all()
    selected_class = None
    
    if selected_class_id:
        selected_class = get_object_or_404(StudentClass, pk=selected_class_id)
    elif classes.exists():
        selected_class = classes.first()
    
    context = {
        'session': session,
        'term': term,
        'classes': classes,
        'selected_class': selected_class,
    }
    
    if not selected_class:
        messages.info(request, 'No classes found. Please create a class first.')
        return render(request, 'result/analytics_dashboard.html', context)
    
    # Calculate class rankings
    rankings = calculate_class_rankings(selected_class, session, term)
    
    # Get top 10 students
    students_with_ranks = []
    for student_id, rank_data in rankings.items():
        student = Student.objects.get(pk=student_id)
        results = Result.objects.filter(
            student=student,
            session=session,
            term=term,
            current_class=selected_class
        )
        gpa = calculate_gpa(results)
        gpa_class = get_gpa_class(gpa)
        
        students_with_ranks.append({
            'student': student,
            'position': rank_data['position'],
            'avg_score': rank_data['avg_score'],
            'gpa': gpa,
            'gpa_class': gpa_class,
        })
    
    # Sort and get top 10
    students_with_ranks.sort(key=lambda x: x['position'])
    top_students = students_with_ranks[:10]
    
    # Subject analytics
    subjects = Subject.objects.all()
    subject_stats = []
    for subject in subjects:
        stats = get_subject_analytics(selected_class, session, term, subject)
        if stats:
            subject_stats.append(stats)
    
    # Class statistics
    all_results = Result.objects.filter(
        current_class=selected_class,
        session=session,
        term=term
    )
    
    class_stats = {
        'total_students': len(rankings),
        'total_results': all_results.count(),
        'avg_class_score': round(
            sum(r.total_score() for r in all_results) / all_results.count(), 2
        ) if all_results.exists() else 0,
        'highest_score': max((r.total_score() for r in all_results), default=0),
        'lowest_score': min((r.total_score() for r in all_results), default=0),
    }
    
    # Performance distribution (for chart)
    grade_distribution = {'Exceeding': 0, 'EE': 0, 'ME': 0, 'AE': 0, 'BE': 0}
    for result in all_results:
        grade = result.grade()
        if grade in grade_distribution:
            grade_distribution[grade] += 1
    
    # Prepare chart data
    chart_data = {
        'grade_labels': list(grade_distribution.keys()),
        'grade_counts': list(grade_distribution.values()),
        'subject_names': [s['subject'] for s in subject_stats],
        'subject_averages': [s['average'] for s in subject_stats],
        'subject_pass_rates': [s['pass_rate'] for s in subject_stats],
    }
    
    context.update({
        'top_students': top_students,
        'subject_stats': subject_stats,
        'class_stats': class_stats,
        'chart_data': json.dumps(chart_data),
        'all_rankings': students_with_ranks,
    })
    
    return render(request, 'result/analytics_dashboard.html', context)


@login_required
def bulk_upload_results(request):
    """
    Bulk upload results from Excel/CSV file.
    """
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            uploaded_file = request.FILES['file']
            session = form.cleaned_data['session']
            term = form.cleaned_data['term']
            student_class = form.cleaned_data['student_class']
            
            # Preview mode or save mode
            if 'preview' in request.POST:
                # Parse file and show preview
                try:
                    preview_data = parse_upload_file(uploaded_file)
                    context = {
                        'form': form,
                        'preview_data': preview_data,
                        'session': session,
                        'term': term,
                        'student_class': student_class,
                    }
                    return render(request, 'result/bulk_upload.html', context)
                except Exception as e:
                    messages.error(request, f'Error parsing file: {str(e)}')
                    
            elif 'confirm' in request.POST:
                # Save the data
                try:
                    preview_data = parse_upload_file(uploaded_file)
                    saved, errors = save_bulk_results(
                        preview_data, session, term, student_class
                    )
                    
                    if saved:
                        messages.success(
                            request,
                            f'Successfully uploaded {saved} results!'
                        )
                    if errors:
                        for error in errors[:5]:  # Show first 5 errors
                            messages.warning(request, error)
                            
                    return redirect('analytics-dashboard')
                except Exception as e:
                    messages.error(request, f'Error saving results: {str(e)}')
    else:
        form = BulkUploadForm()
    
    context = {'form': form}
    return render(request, 'result/bulk_upload.html', context)


def parse_upload_file(uploaded_file):
    """
    Parse Excel or CSV file and return list of dicts.
    Expected columns: Registration Number, Subject, CA Score, Exam Score
    """
    file_ext = uploaded_file.name.split('.')[-1].lower()
    
    if file_ext == 'csv':
        # Parse CSV
        file_data = TextIOWrapper(uploaded_file.file, encoding='utf-8')
        csv_reader = csv.DictReader(file_data)
        data = list(csv_reader)
    
    elif file_ext in ['xlsx', 'xls']:
        # Parse Excel
        try:
            import pandas as pd
            df = pd.read_excel(uploaded_file)
            # Convert to list of dicts
            data = df.to_dict('records')
        except ImportError:
            raise Exception(
                "pandas and openpyxl are required for Excel upload. "
                "Install with: pip install pandas openpyxl"
            )
    
    else:
        raise Exception(f"Unsupported file format: {file_ext}")

    # Normalize keys to snake_case for template compatibility
    normalized_data = []
    for row in data:
        normalized_row = {}
        for key, value in row.items():
            # Convert "Registration Number" to "registration_number"
            new_key = key.strip().lower().replace(' ', '_')
            normalized_row[new_key] = value
        normalized_data.append(normalized_row)
        
    return normalized_data


def save_bulk_results(data, session, term, student_class):
    """
    Save bulk results from parsed data.
    Returns (count_saved, list_of_errors).
    """
    saved_count = 0
    errors = []
    
    for idx, row in enumerate(data, start=2):  # Start at 2 (row 1 is header)
        try:
            # Get student
            reg_no = str(row.get('registration_number', '')).strip()
            if not reg_no:
                errors.append(f'Row {idx}: Missing registration number')
                continue
                
            student = Student.objects.filter(
                registration_number__iexact=reg_no
            ).first()
            
            if not student:
                errors.append(f'Row {idx}: Student {reg_no} not found')
                continue
            
            # Get subject
            subject_name = str(row.get('subject', '')).strip()
            if not subject_name:
                errors.append(f'Row {idx}: Missing subject')
                continue
                
            subject = Subject.objects.filter(name__iexact=subject_name).first()
            if not subject:
                errors.append(f'Row {idx}: Subject "{subject_name}" not found')
                continue
            
            # Get scores
            try:
                ca_score = int(row.get('ca_score', 0))
                exam_score = int(row.get('exam_score', 0))
            except (ValueError, TypeError):
                errors.append(f'Row {idx}: Invalid score values')
                continue
            
            # Validate scores
            if ca_score < 0 or ca_score > 40:
                errors.append(f'Row {idx}: CA score must be 0-40')
                continue
            if exam_score < 0 or exam_score > 60:
                errors.append(f'Row {idx}: Exam score must be 0-60')
                continue
            
            # Create or update result
            result, created = Result.objects.update_or_create(
                student=student,
                session=session,
                term=term,
                current_class=student_class,
                subject=subject,
                defaults={
                    'test_score': ca_score,
                    'exam_score': exam_score,
                }
            )
            
            saved_count += 1
            
        except Exception as e:
            errors.append(f'Row {idx}: {str(e)}')
            continue
    
    return saved_count, errors


@login_required
def download_bulk_template(request):
    """Download Excel template for bulk upload."""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="bulk_results_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Registration Number', 'Subject', 'CA Score', 'Exam Score'])
    writer.writerow(['ST001', 'Mathematics', '35', '55'])
    writer.writerow(['ST001', 'English', '38', '52'])
    writer.writerow(['ST002', 'Mathematics', '32', '48'])
    
    return response
