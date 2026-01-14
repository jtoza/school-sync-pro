from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import csv

from apps.corecode.models import StudentClass, AcademicTerm, AcademicSession
from apps.students.models import Student
from apps.staffs.models import Staff, TeacherAttendance
from django.core.paginator import Paginator

from .forms import AttendanceRegisterForm, AttendanceEntryForm, BulkRegisterForm, DailyAttendanceConfigForm
from .models import AttendanceRegister, AttendanceEntry, AttendanceSummary, DailyAttendanceConfig


class AttendanceRegisterListView(LoginRequiredMixin, ListView):
    model = AttendanceRegister
    template_name = 'attendance/register_list.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class if provided
        class_filter = self.request.GET.get('class')
        if class_filter:
            queryset = queryset.filter(student_class_id=class_filter)
        
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.select_related('student_class', 'term', 'session', 'taken_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = StudentClass.objects.all()
        return context


class AttendanceRegisterCreateView(LoginRequiredMixin, CreateView):
    model = AttendanceRegister
    form_class = AttendanceRegisterForm
    template_name = 'attendance/register_form.html'
    success_url = reverse_lazy('attendance:register_list')

    def form_valid(self, form):
        form.instance.taken_by = self.request.user
        
        # Check if register already exists
        existing = AttendanceRegister.objects.filter(
            date=form.instance.date,
            student_class=form.instance.student_class,
            term=form.instance.term,
            session=form.instance.session
        ).exists()
        
        if existing:
            messages.error(self.request, 'Attendance register for this class and date already exists.')
            return self.form_invalid(form)
        
        messages.success(self.request, 'Attendance register created successfully.')
        return super().form_valid(form)


class AttendanceRegisterDetailView(LoginRequiredMixin, DetailView):
    model = AttendanceRegister
    template_name = 'attendance/register_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        register = self.object
        
        # Add statistics
        context['present_count'] = register.present_count
        context['absent_count'] = register.absent_count
        context['late_count'] = register.late_count
        context['attendance_rate'] = register.attendance_rate
        
        return context


class AttendanceRegisterUpdateView(LoginRequiredMixin, UpdateView):
    model = AttendanceRegister
    form_class = AttendanceRegisterForm
    template_name = 'attendance/register_form.html'
    success_url = reverse_lazy('attendance:register_list')

    def form_valid(self, form):
        messages.success(self.request, 'Attendance register updated successfully.')
        return super().form_valid(form)


class AttendanceRegisterDeleteView(LoginRequiredMixin, DeleteView):
    model = AttendanceRegister
    template_name = 'attendance/register_confirm_delete.html'
    success_url = reverse_lazy('attendance:register_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Attendance register deleted successfully.')
        return super().delete(request, *args, **kwargs)


class BulkRegisterCreateView(LoginRequiredMixin, View):
    template_name = 'attendance/bulk_register_create.html'

    def get(self, request):
        form = BulkRegisterForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = BulkRegisterForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            student_class = form.cleaned_data['student_class']
            term = form.cleaned_data['term']
            session = form.cleaned_data['session']

            current_date = start_date
            registers_created = 0
            
            while current_date <= end_date:
                # Skip weekends (optional - you can remove this)
                if current_date.weekday() < 5:  # 0-4 = Monday-Friday
                    # Check if register already exists
                    exists = AttendanceRegister.objects.filter(
                        date=current_date,
                        student_class=student_class,
                        term=term,
                        session=session
                    ).exists()
                    
                    if not exists:
                        AttendanceRegister.objects.create(
                            date=current_date,
                            student_class=student_class,
                            term=term,
                            session=session,
                            taken_by=request.user,
                            auto_created=True,
                            notes=f'Auto-created bulk register'
                        )
                        registers_created += 1
                
                current_date += timedelta(days=1)
            
            messages.success(request, f'Successfully created {registers_created} attendance registers.')
            return redirect('attendance:register_list')
        
        return render(request, self.template_name, {'form': form})


@login_required
def take_attendance(request, pk):
    register = get_object_or_404(AttendanceRegister, pk=pk)
    
    # Check if register is locked
    if register.is_locked:
        messages.error(request, 'This attendance register is locked and cannot be modified.')
        return redirect('attendance:register_detail', pk=register.pk)
    
    students = Student.objects.filter(
        current_class=register.student_class, 
        current_status='active'
    ).order_by('surname', 'firstname')

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', AttendanceEntry.STATUS_PRESENT)
            remarks = request.POST.get(f'remarks_{student.id}', '')
            time_in = request.POST.get(f'time_in_{student.id}', '')
            time_out = request.POST.get(f'time_out_{student.id}', '')
            
            entry, created = AttendanceEntry.objects.get_or_create(
                register=register, 
                student=student
            )
            entry.status = status
            entry.remarks = remarks
            entry.time_in = time_in if time_in else None
            entry.time_out = time_out if time_out else None
            entry.save()
        
        messages.success(request, 'Attendance saved successfully!')
        return redirect('attendance:register_detail', pk=register.pk)

    entries = {e.student_id: e for e in AttendanceEntry.objects.filter(register=register)}

    context = {
        'register': register,
        'students': students,
        'entries': entries,
        'status_choices': AttendanceEntry.STATUS_CHOICES,
    }
    return render(request, 'attendance/take_attendance.html', context)


@login_required
def lock_register(request, pk):
    register = get_object_or_404(AttendanceRegister, pk=pk)
    register.is_locked = True
    register.save()
    messages.success(request, 'Attendance register locked successfully.')
    return redirect('attendance:register_detail', pk=register.pk)


@login_required
def unlock_register(request, pk):
    register = get_object_or_404(AttendanceRegister, pk=pk)
    register.is_locked = False
    register.save()
    messages.success(request, 'Attendance register unlocked successfully.')
    return redirect('attendance:register_detail', pk=register.pk)


class AttendanceReportView(LoginRequiredMixin, View):
    template_name = 'attendance/attendance_reports.html'

    def get(self, request):
        classes = StudentClass.objects.all()
        terms = AcademicTerm.objects.all()
        sessions = AcademicSession.objects.all()
        
        # Default to current term and session
        current_term = AcademicTerm.objects.filter(current=True).first()
        current_session = AcademicSession.objects.filter(current=True).first()
        
        context = {
            'classes': classes,
            'terms': terms,
            'sessions': sessions,
            'current_term': current_term,
            'current_session': current_session,
        }
        return render(request, self.template_name, context)


@login_required
def attendance_summary_data(request):
    """AJAX endpoint for attendance summary data"""
    class_id = request.GET.get('class')
    term_id = request.GET.get('term')
    session_id = request.GET.get('session')
    
    # Get registers for the filters
    registers = AttendanceRegister.objects.all()
    
    if class_id:
        registers = registers.filter(student_class_id=class_id)
    if term_id:
        registers = registers.filter(term_id=term_id)
    if session_id:
        registers = registers.filter(session_id=session_id)
    
    total_registers = registers.count()
    if total_registers == 0:
        return JsonResponse({'error': 'No data found for the selected filters'})
    
    # Calculate averages
    total_students = 0
    total_present = 0
    total_absent = 0
    total_late = 0
    
    for register in registers:
        total_students += register.total_students
        total_present += register.present_count
        total_absent += register.absent_count
        total_late += register.late_count
    
    avg_attendance_rate = round((total_present / total_students) * 100, 2) if total_students > 0 else 0
    
    data = {
        'total_registers': total_registers,
        'total_students': total_students,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'avg_attendance_rate': avg_attendance_rate,
    }
    
    return JsonResponse(data)


class DailyAttendanceDashboard(LoginRequiredMixin, View):
    template_name = 'attendance/daily_dashboard.html'

    def get(self, request):
        today = timezone.now().date()
        
        # Get today's registers for classes taught by current user
        today_registers = AttendanceRegister.objects.filter(date=today)
        
        # Get recent registers
        recent_registers = AttendanceRegister.objects.filter(
            date__lt=today
        ).order_by('-date')[:5]
        
        # Statistics
        total_classes = StudentClass.objects.count()
        registers_today = today_registers.count()
        pending_today = total_classes - registers_today
        
        context = {
            'today': today,
            'today_registers': today_registers,
            'recent_registers': recent_registers,
            'total_classes': total_classes,
            'registers_today': registers_today,
            'pending_today': pending_today,
        }
        return render(request, self.template_name, context)


class AttendanceHistoryView(LoginRequiredMixin, View):
    template_name = 'attendance/history.html'

    def get(self, request):
        # Teacher filters
        teacher_id = request.GET.get('teacher')
        t_month = request.GET.get('t_month')
        t_status = request.GET.get('t_status')

        teacher_qs = TeacherAttendance.objects.select_related('teacher').all().order_by('-date', 'teacher__surname')
        if teacher_id:
            teacher_qs = teacher_qs.filter(teacher_id=teacher_id)
        if t_month:
            teacher_qs = teacher_qs.filter(date__month=t_month)
        if t_status:
            teacher_qs = teacher_qs.filter(status=t_status)

        t_paginator = Paginator(teacher_qs, 20)
        t_page = request.GET.get('t_page')
        t_page_obj = t_paginator.get_page(t_page)

        # Student filters
        s_class = request.GET.get('s_class')
        s_date_from = request.GET.get('s_date_from')
        s_date_to = request.GET.get('s_date_to')
        s_locked = request.GET.get('s_locked')  # 'locked', 'open' or ''

        register_qs = AttendanceRegister.objects.select_related('student_class', 'term', 'session').all().order_by('-date', 'student_class__name')
        if s_class:
            register_qs = register_qs.filter(student_class_id=s_class)
        if s_date_from:
            register_qs = register_qs.filter(date__gte=s_date_from)
        if s_date_to:
            register_qs = register_qs.filter(date__lte=s_date_to)
        if s_locked == 'locked':
            register_qs = register_qs.filter(is_locked=True)
        elif s_locked == 'open':
            register_qs = register_qs.filter(is_locked=False)

        s_paginator = Paginator(register_qs, 20)
        s_page = request.GET.get('s_page')
        s_page_obj = s_paginator.get_page(s_page)

        context = {
            't_page_obj': t_page_obj,
            's_page_obj': s_page_obj,
            'teachers': Staff.objects.filter(current_status='active'),
            'classes': StudentClass.objects.all(),
            'filters': {
                'teacher': teacher_id,
                't_month': t_month,
                't_status': t_status,
                's_class': s_class,
                's_date_from': s_date_from,
                's_date_to': s_date_to,
                's_locked': s_locked,
            }
        }
        return render(request, self.template_name, context)