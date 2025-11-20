from django.contrib.messages.views import SuccessMessageMixin
from django.forms import widgets
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, date

from .models import Staff, TeacherAttendance


class StaffListView(ListView):
    model = Staff
    template_name = "staffs/staff_list.html"


class StaffDetailView(DetailView):
    model = Staff
    template_name = "staffs/staff_detail.html"


class StaffCreateView(SuccessMessageMixin, CreateView):
    model = Staff
    fields = "__all__"
    success_message = "New staff successfully added"

    def get_form(self):
        """add date picker in forms"""
        form = super(StaffCreateView, self).get_form()
        form.fields["date_of_birth"].widget = widgets.DateInput(attrs={"type": "date"})
        form.fields["date_of_admission"].widget = widgets.DateInput(
            attrs={"type": "date"}
        )
        form.fields["address"].widget = widgets.Textarea(attrs={"rows": 1})
        form.fields["others"].widget = widgets.Textarea(attrs={"rows": 1})
        return form


class StaffUpdateView(SuccessMessageMixin, UpdateView):
    model = Staff
    fields = "__all__"
    success_message = "Record successfully updated."

    def get_form(self):
        """add date picker in forms"""
        form = super(StaffUpdateView, self).get_form()
        form.fields["date_of_birth"].widget = widgets.DateInput(attrs={"type": "date"})
        form.fields["date_of_admission"].widget = widgets.DateInput(
            attrs={"type": "date"}
        )
        form.fields["address"].widget = widgets.Textarea(attrs={"rows": 1})
        form.fields["others"].widget = widgets.Textarea(attrs={"rows": 1})
        return form


class StaffDeleteView(DeleteView):
    model = Staff
    success_url = reverse_lazy("staff-list")
    template_name = "staffs/staff_confirm_delete.html"


# ============================
# TEACHER ATTENDANCE VIEWS
# ============================

@login_required
def teacher_attendance_dashboard(request):
    """Teacher Attendance Dashboard"""
    today = timezone.now().date()
    
    # Get today's attendance stats
    today_attendance = TeacherAttendance.objects.filter(date=today)
    present_count = today_attendance.filter(status='present').count()
    absent_count = today_attendance.filter(status='absent').count()
    late_count = today_attendance.filter(status='late').count()
    total_teachers = Staff.objects.filter(current_status='active').count()
    
    context = {
        'today': today,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'total_teachers': total_teachers,
        'attendance_percentage': (present_count / total_teachers * 100) if total_teachers > 0 else 0,
    }
    return render(request, 'staffs/attendance_dashboard.html', context)


@login_required
def mark_attendance(request):
    """Mark attendance for teachers"""
    today = timezone.now().date()
    teachers = Staff.objects.filter(current_status='active')
    
    if request.method == 'POST':
        date_str = request.POST.get('attendance_date', today.isoformat())
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        for teacher in teachers:
            status = request.POST.get(f'status_{teacher.id}', 'absent')
            time_in = request.POST.get(f'time_in_{teacher.id}', '')
            time_out = request.POST.get(f'time_out_{teacher.id}', '')
            notes = request.POST.get(f'notes_{teacher.id}', '')
            
            # Create or update attendance record
            attendance, created = TeacherAttendance.objects.update_or_create(
                teacher=teacher,
                date=attendance_date,
                defaults={
                    'status': status,
                    'time_in': time_in if time_in else None,
                    'time_out': time_out if time_out else None,
                    'notes': notes,
                }
            )
        
        messages.success(request, f'Attendance marked successfully for {attendance_date}')
        return redirect('staffs:attendance-dashboard')
    
    # GET request - show form
    selected_date = request.GET.get('date', today.isoformat())
    attendance_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    # Get existing attendance records for the selected date
    existing_attendance = TeacherAttendance.objects.filter(date=attendance_date)
    attendance_dict = {att.teacher.id: att for att in existing_attendance}
    
    context = {
        'teachers': teachers,
        'selected_date': attendance_date,
        'attendance_dict': attendance_dict,
        'today': today,
    }
    return render(request, 'staffs/mark_attendance.html', context)


@login_required
def attendance_records(request):
    """View attendance records"""
    records = TeacherAttendance.objects.select_related('teacher').all()
    
    # Filtering
    teacher_id = request.GET.get('teacher')
    month = request.GET.get('month')
    status = request.GET.get('status')
    
    if teacher_id:
        records = records.filter(teacher_id=teacher_id)
    if month:
        records = records.filter(date__month=month)
    if status:
        records = records.filter(status=status)
    
    # Pagination
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    teachers = Staff.objects.filter(current_status='active')
    
    context = {
        'page_obj': page_obj,
        'teachers': teachers,
        'selected_teacher': teacher_id,
        'selected_month': month,
        'selected_status': status,
    }
    return render(request, 'staffs/attendance_records.html', context)


# Custom template filter for the mark_attendance template
def get_item(dictionary, key):
    return dictionary.get(key)

# Register the custom filter (you'll need to add this to a templatetags folder or use an alternative approach)
# For now, we'll handle it in the template differently