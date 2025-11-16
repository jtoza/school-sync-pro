from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

from .models import StudentClass
from apps.students.models import Student

@login_required
def teacher_class_list(request):
    """Show classes managed by the current teacher"""
    # Allow ALL logged-in users to access (teachers, admins, staff, etc.)
    managed_classes = StudentClass.objects.all()
    
    context = {
        'managed_classes': managed_classes,
        'is_teacher': request.user.groups.filter(name='Teachers').exists(),
        'is_superuser': request.user.is_superuser,
        'is_staff': request.user.is_staff,
    }
    return render(request, 'corecode/teacher_class_list.html', context)

@login_required
def class_detail(request, class_id):
    """Detailed view of a specific class with students and quick actions"""
    student_class = get_object_or_404(StudentClass, id=class_id)
    
    # Allow ALL logged-in users to view class details
    # Get students in this class
    students = Student.objects.filter(current_class=student_class, current_status='active')
    
    context = {
        'student_class': student_class,
        'students': students,
        'student_count': students.count(),
    }
    return render(request, 'corecode/class_detail.html', context)