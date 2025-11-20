from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import os
from apps.students.models import Student
from apps.corecode.models import StudentClass
from apps.staffs.models import Staff 
from .models import StudentIDCard, IDCardTemplate, TeacherIDCard
from .utils import generate_student_id, generate_barcode
from django.views.generic import View

@login_required
def idcard_dashboard(request):
    """ID Card Management Dashboard"""
    total_students = Student.objects.filter(current_status='active').count()
    idcards_generated = StudentIDCard.objects.count()
    expired_cards = StudentIDCard.objects.filter(expiry_date__lt=timezone.now().date()).count()
    
    # Calculate coverage percentage
    coverage_percentage = (idcards_generated / total_students * 100) if total_students > 0 else 0
    
    context = {
        'total_students': total_students,
        'idcards_generated': idcards_generated,
        'expired_cards': expired_cards,
        'coverage_percentage': round(coverage_percentage, 1),
    }
    return render(request, 'idcards/dashboard.html', context)

@login_required
def generate_id_card(request, student_id):
    """Generate ID card for individual student"""
    student = get_object_or_404(Student, id=student_id)
    
    # Create or get existing ID card
    id_card, created = StudentIDCard.objects.get_or_create(
        student=student,
        defaults={
            'id_number': generate_student_id(),
            'expiry_date': timezone.now().date() + timedelta(days=365),
            'template_used': 'default'
        }
    )
    
    if created:
        messages.success(request, f'ID card created for {student.get_full_name()}')
    
    context = {
        'student': student,
        'id_card': id_card,
        'school_name': 'GREEN BELLS ACADEMY',
        'school_motto': 'IN PURSUIT OF EXCELLENCE',
        'today': timezone.now().date(),
    }
    return render(request, 'idcards/id_card_preview.html', context)

@login_required
def bulk_generate_id_cards(request):
    """Bulk generate ID cards for all active students"""
    if request.method == 'POST':
        scope = request.POST.get('scope', 'all')
        class_id = request.POST.get('class_id')
        
        # Determine which students to process
        if scope == 'class' and class_id:
            student_class = get_object_or_404(StudentClass, id=class_id)
            students = Student.objects.filter(current_class=student_class, current_status='active')
        else:
            students = Student.objects.filter(current_status='active')
        
        generated_count = 0
        for student in students:
            # Check if student already has an ID card
            if not StudentIDCard.objects.filter(student=student).exists():
                id_card, created = StudentIDCard.objects.get_or_create(
                    student=student,
                    defaults={
                        'id_number': generate_student_id(),
                        'expiry_date': timezone.now().date() + timedelta(days=365),
                        'template_used': 'default'
                    }
                )
                if created:
                    generated_count += 1
        
        if generated_count > 0:
            messages.success(request, f'Successfully generated {generated_count} new ID cards')
        else:
            messages.info(request, 'No new ID cards were generated. All selected students already have ID cards.')
        
        return redirect('idcards:idcard-list')
    
    # GET request - show student selection
    students = Student.objects.filter(current_status='active')
    classes = StudentClass.objects.all()
    
    # Add statistics for the template
    total_students = students.count()
    generated_count = StudentIDCard.objects.count()
    pending_count = total_students - generated_count
    coverage_percentage = (generated_count / total_students * 100) if total_students > 0 else 0
    
    context = {
        'students': students,
        'classes': classes,
        'total_students': total_students,
        'generated_count': generated_count,
        'pending_count': pending_count,
        'coverage_percentage': round(coverage_percentage, 1),
    }
    return render(request, 'idcards/bulk_generate.html', context)

@login_required
def bulk_generate_class_id_cards(request, class_id):
    """Generate ID cards for entire class"""
    student_class = get_object_or_404(StudentClass, id=class_id)
    students = Student.objects.filter(current_class=student_class, current_status='active')
    
    generated_cards = []
    for student in students:
        id_card, created = StudentIDCard.objects.get_or_create(
            student=student,
            defaults={
                'id_number': generate_student_id(),
                'expiry_date': timezone.now().date() + timedelta(days=365),
                'template_used': 'default'
            }
        )
        
        if created:
            generated_cards.append(id_card)
    
    messages.success(request, f'Generated ID cards for {len(generated_cards)} students in {student_class.name}')
    
    context = {
        'generated_cards': generated_cards,
        'student_class': student_class,
        'today': timezone.now().date(),
    }
    return render(request, 'idcards/bulk_generation_result.html', context)

@login_required
def download_id_card_pdf(request, student_id):
    """Download individual ID card as PDF"""
    # Import inside function to avoid circular imports
    try:
        from apps.result.views import render_to_pdf
    except ImportError:
        messages.error(request, 'PDF generation is not available')
        return redirect('idcards:generate-idcard', student_id=student_id)
    
    student = get_object_or_404(Student, id=student_id)
    id_card = get_object_or_404(StudentIDCard, student=student)
    
    context = {
        'student': student,
        'id_card': id_card,
        'school_name': 'GREEN BELLS ACADEMY',
        'school_motto': 'IN PURSUIT OF EXCELLENCE',
        'today': timezone.now().date(),
    }
    
    response = render_to_pdf(request, 'idcards/id_card_pdf.html', context)
    if response:
        filename = f"id_card_{student.registration_number}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Failed to generate PDF')
        return redirect('idcards:generate-idcard', student_id=student_id)

@login_required
def download_bulk_id_cards(request):
    """Download multiple ID cards as ZIP"""
    # This is a placeholder - you can implement ZIP generation later
    messages.info(request, 'Bulk download feature coming soon!')
    return redirect('idcards:idcard-list')

@login_required
def manage_templates(request):
    """Manage ID card templates"""
    templates = IDCardTemplate.objects.all()
    
    context = {
        'templates': templates,
    }
    return render(request, 'idcards/manage_templates.html', context)

@login_required
def idcard_list(request):
    """List all ID cards"""
    idcards_list = StudentIDCard.objects.select_related('student').all()
    
    # Pagination
    paginator = Paginator(idcards_list, 12)  # 12 cards per page
    page_number = request.GET.get('page')
    idcards = paginator.get_page(page_number)
    
    classes = StudentClass.objects.all()
    
    context = {
        'idcards': idcards,
        'classes': classes,
        'today': timezone.now().date(),
    }
    return render(request, 'idcards/idcard_list.html', context)

@login_required
def renew_id_card(request, student_id):
    """Renew an expired ID card"""
    student = get_object_or_404(Student, id=student_id)
    id_card = get_object_or_404(StudentIDCard, student=student)
    
    # Renew the card by updating expiry date
    id_card.expiry_date = timezone.now().date() + timedelta(days=365)
    id_card.is_active = True
    id_card.save()
    
    messages.success(request, f'ID card renewed for {student.get_full_name()}. Valid until {id_card.expiry_date}')
    return redirect('idcards:generate-idcard', student_id=student_id)

class IDCardSearchView(View):
    def get(self, request):
        return render(request, 'idcards/idcard_search.html')
    
    def post(self, request):
        registration_number = request.POST.get('registration_number', '').strip()
        
        if not registration_number:
            messages.error(request, 'Please enter a registration number')
            return render(request, 'idcards/idcard_search.html')
        
        try:
            # Find student by registration number
            student = Student.objects.get(registration_number=registration_number)
            # Redirect to the ID card generation page for this student
            return redirect('idcards:generate-idcard', student_id=student.id)
            
        except Student.DoesNotExist:
            messages.error(request, f'Student with registration number "{registration_number}" not found')
            return render(request, 'idcards/idcard_search.html')

@login_required
def generate_teacher_id_card(request, teacher_id):
    """Generate ID card for individual teacher"""
    teacher = get_object_or_404(Staff, id=teacher_id)
    
    # Create or get existing ID card
    id_card, created = TeacherIDCard.objects.get_or_create(
        teacher=teacher,
        defaults={
            'id_number': f"TEA{generate_student_id()[3:]}",  # Teacher ID prefix
            'expiry_date': timezone.now().date() + timedelta(days=365),
            'template_used': 'default'
        }
    )
    
    if created:
        messages.success(request, f'ID card created for Teacher {teacher.firstname} {teacher.surname}')
    
    context = {
        'teacher': teacher,
        'id_card': id_card,
        'school_name': 'GREEN BELLS ACADEMY',
        'school_motto': 'IN PURSUIT OF EXCELLENCE',
        'today': timezone.now().date(),
    }
    return render(request, 'idcards/teacher_id_card_preview.html', context)

@login_required
def bulk_generate_teacher_id_cards(request):
    """Bulk generate ID cards for all teachers"""
    if request.method == 'POST':
        scope = request.POST.get('scope', 'all')
        
        # Get active teachers - FIXED: Use current_status instead of is_active
        teachers = Staff.objects.filter(current_status='active')
        
        generated_count = 0
        for teacher in teachers:
            # Check if teacher already has an ID card
            if not TeacherIDCard.objects.filter(teacher=teacher).exists():
                id_card, created = TeacherIDCard.objects.get_or_create(
                    teacher=teacher,
                    defaults={
                        'id_number': f"TEA{generate_student_id()[3:]}",
                        'expiry_date': timezone.now().date() + timedelta(days=365),
                        'template_used': 'default'
                    }
                )
                if created:
                    generated_count += 1
        
        if generated_count > 0:
            messages.success(request, f'Successfully generated {generated_count} new teacher ID cards')
        else:
            messages.info(request, 'No new teacher ID cards were generated. All teachers already have ID cards.')
        
        return redirect('idcards:teacher-idcard-list')
    
    # GET request - show statistics
    # FIXED: Use current_status instead of is_active
    total_teachers = Staff.objects.filter(current_status='active').count()
    generated_count = TeacherIDCard.objects.count()
    pending_count = total_teachers - generated_count
    coverage_percentage = (generated_count / total_teachers * 100) if total_teachers > 0 else 0
    
    context = {
        'total_teachers': total_teachers,
        'generated_count': generated_count,
        'pending_count': pending_count,
        'coverage_percentage': round(coverage_percentage, 1),
    }
    return render(request, 'idcards/bulk_generate_teachers.html', context)

@login_required
def teacher_idcard_list(request):
    """List all teacher ID cards"""
    idcards_list = TeacherIDCard.objects.select_related('teacher').all()
    
    # Pagination
    paginator = Paginator(idcards_list, 12)
    page_number = request.GET.get('page')
    idcards = paginator.get_page(page_number)
    
    context = {
        'idcards': idcards,
        'today': timezone.now().date(),
    }
    return render(request, 'idcards/teacher_idcard_list.html', context) 

@login_required
def download_teacher_id_card_pdf(request, teacher_id):
    """Download individual teacher ID card as PDF"""
    try:
        from apps.result.views import render_to_pdf
    except ImportError:
        messages.error(request, 'PDF generation is not available')
        return redirect('idcards:generate-teacher-idcard', teacher_id=teacher_id)
    
    teacher = get_object_or_404(Staff, id=teacher_id)
    id_card = get_object_or_404(TeacherIDCard, teacher=teacher)
    
    # Get the base URL for absolute image paths
    base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
    
    context = {
        'teacher': teacher,
        'id_card': id_card,
        'school_name': 'GREEN BELLS ACADEMY',
        'school_motto': 'IN PURSUIT OF EXCELLENCE',
        'today': timezone.now().date(),
        'base_url': base_url,  # Add base URL for absolute image paths
    }
    
    response = render_to_pdf(request, 'idcards/teacher_id_card_pdf.html', context)
    if response:
        filename = f"teacher_id_card_{teacher.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Failed to generate PDF')
        return redirect('idcards:generate-teacher-idcard', teacher_id=teacher_id) 

@login_required
def renew_teacher_id_card(request, teacher_id):
    """Renew an expired teacher ID card"""
    teacher = get_object_or_404(Staff, id=teacher_id)
    id_card = get_object_or_404(TeacherIDCard, teacher=teacher)
    
    # Renew the card by updating expiry date
    id_card.expiry_date = timezone.now().date() + timedelta(days=365)
    id_card.is_active = True
    id_card.save()
    
    messages.success(request, f'ID card renewed for Teacher {teacher.firstname} {teacher.surname}. Valid until {id_card.expiry_date}')
    return redirect('idcards:generate-teacher-idcard', teacher_id=teacher_id)