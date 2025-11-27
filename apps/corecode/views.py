from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils import timezone

from .forms import (
    AcademicSessionForm,
    AcademicTermForm,
    CurrentSessionForm,
    SiteConfigForm,
    StudentClassForm,
    SubjectForm,
)
from .models import (
    AcademicSession,
    AcademicTerm,
    SiteConfig,
    StudentClass,
    Subject,
)


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Live dashboard stats
        try:
            from apps.students.models import Student
            from apps.staffs.models import Staff
            from .models import StudentClass
            from apps.finance.models import Receipt
            from django.utils import timezone
            from django.db.models import Sum

            student_count = Student.objects.filter(current_status='active').count()
            staff_active = Staff.objects.filter(current_status='active').count()
            class_count = StudentClass.objects.count()
            now = timezone.now()
            revenue_month = Receipt.objects.filter(date_paid__year=now.year, date_paid__month=now.month).aggregate(s=Sum('amount_paid'))['s'] or 0
        except Exception:
            student_count = staff_active = class_count = 0
            revenue_month = 0
        context['dashboard'] = {
            'student_count': student_count,
            'staff_active': staff_active,
            'class_count': class_count,
            'revenue_month': revenue_month,
        }
        return context


class SiteConfigView(LoginRequiredMixin, View):
    """Site Config View"""

    form_class = SiteConfigForm
    template_name = "corecode/siteconfig.html"

    def get(self, request, *args, **kwargs):
        formset = self.form_class(queryset=SiteConfig.objects.all())
        context = {"formset": formset}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        formset = self.form_class(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Configurations successfully updated")
        context = {"formset": formset, "title": "Configuration"}
        return render(request, self.template_name, context)


class SessionListView(LoginRequiredMixin, SuccessMessageMixin, ListView):
    model = AcademicSession
    template_name = "corecode/session_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AcademicSessionForm()
        return context


class SessionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    template_name = "corecode/mgt_form.html"
    success_url = reverse_lazy("sessions")
    success_message = "New session successfully added"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add new session"
        return context


class SessionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AcademicSession
    form_class = AcademicSessionForm
    success_url = reverse_lazy("sessions")
    success_message = "Session successfully updated."
    template_name = "corecode/mgt_form.html"

    def form_valid(self, form):
        obj = self.object
        if obj.current == False:
            terms = (
                AcademicSession.objects.filter(current=True)
                .exclude(name=obj.name)
                .exists()
            )
            if not terms:
                messages.warning(self.request, "You must set a session to current.")
                return redirect("session-list")
        return super().form_valid(form)


class SessionDeleteView(LoginRequiredMixin, DeleteView):
    model = AcademicSession
    success_url = reverse_lazy("sessions")
    template_name = "corecode/core_confirm_delete.html"
    success_message = "The session {} has been deleted with all its attached content"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.current == True:
            messages.warning(request, "Cannot delete session as it is set to current")
            return redirect("sessions")
        messages.success(self.request, self.success_message.format(obj.name))
        return super(SessionDeleteView, self).delete(request, *args, **kwargs)


class TermListView(LoginRequiredMixin, SuccessMessageMixin, ListView):
    model = AcademicTerm
    template_name = "corecode/term_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AcademicTermForm()
        return context


class TermCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = AcademicTerm
    form_class = AcademicTermForm
    template_name = "corecode/mgt_form.html"
    success_url = reverse_lazy("terms")
    success_message = "New term successfully added"


class TermUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AcademicTerm
    form_class = AcademicTermForm
    success_url = reverse_lazy("terms")
    success_message = "Term successfully updated."
    template_name = "corecode/mgt_form.html"

    def form_valid(self, form):
        obj = self.object
        if obj.current == False:
            terms = (
                AcademicTerm.objects.filter(current=True)
                .exclude(name=obj.name)
                .exists()
            )
            if not terms:
                messages.warning(self.request, "You must set a term to current.")
                return redirect("terms")
        return super().form_valid(form)


class TermDeleteView(LoginRequiredMixin, DeleteView):
    model = AcademicTerm
    success_url = reverse_lazy("terms")
    template_name = "corecode/core_confirm_delete.html"
    success_message = "The term {} has been deleted with all its attached content"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.current == True:
            messages.warning(request, "Cannot delete term as it is set to current")
            return redirect("terms")
        messages.success(self.request, self.success_message.format(obj.name))
        return super(TermDeleteView, self).delete(request, *args, **kwargs)


class ClassListView(LoginRequiredMixin, SuccessMessageMixin, ListView):
    model = StudentClass
    template_name = "corecode/class_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = StudentClassForm()
        return context


# In your views.py file, replace the existing ClassCreateView with this:

class ClassCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = StudentClass
    form_class = StudentClassForm
    template_name = "corecode/mgt_form.html"
    success_url = reverse_lazy("classes")
    success_message = "New class successfully added"

    def form_valid(self, form):
        """Handle AJAX requests differently"""
        response = super().form_valid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': str(self.success_message)
            })
        else:
            messages.success(self.request, self.success_message)
            return response

    def form_invalid(self, form):
        """Handle AJAX form errors"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            })
        else:
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Ensure we can still access the form in regular requests"""
        context = super().get_context_data(**kwargs)
        if not self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            context['title'] = "Add new class"
        return context


class ClassUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = StudentClass
    fields = ["name"]
    success_url = reverse_lazy("classes")
    success_message = "class successfully updated."
    template_name = "corecode/mgt_form.html"


class ClassDeleteView(LoginRequiredMixin, DeleteView):
    model = StudentClass
    success_url = reverse_lazy("classes")
    template_name = "corecode/core_confirm_delete.html"
    success_message = "The class {} has been deleted with all its attached content"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        print(obj.name)
        messages.success(self.request, self.success_message.format(obj.name))
        return super(ClassDeleteView, self).delete(request, *args, **kwargs)


class SubjectListView(LoginRequiredMixin, SuccessMessageMixin, ListView):
    model = Subject
    template_name = "corecode/subject_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SubjectForm()
        return context


class SubjectCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "corecode/mgt_form.html"
    success_url = reverse_lazy("subjects")
    success_message = "New subject successfully added"


class SubjectUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Subject
    fields = ["name"]
    success_url = reverse_lazy("subjects")
    success_message = "Subject successfully updated."
    template_name = "corecode/mgt_form.html"


class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    success_url = reverse_lazy("subjects")
    template_name = "corecode/core_confirm_delete.html"
    success_message = "The subject {} has been deleted with all its attached content"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, self.success_message.format(obj.name))
        return super(SubjectDeleteView, self).delete(request, *args, **kwargs)


class CurrentSessionAndTermView(LoginRequiredMixin, View):
    """Current Session and Term"""

    form_class = CurrentSessionForm
    template_name = "corecode/current_session.html"

    def get(self, request, *args, **kwargs):
        try:
            current_session = AcademicSession.objects.get(current=True)
            current_term = AcademicTerm.objects.get(current=True)
            form = self.form_class(
                initial={
                    "current_session": current_session,
                    "current_term": current_term,
                }
            )
        except (AcademicSession.DoesNotExist, AcademicTerm.DoesNotExist):
            form = self.form_class()
            messages.warning(request, "Please set current session and term first.")
        
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            session = form.cleaned_data["current_session"]
            term = form.cleaned_data["current_term"]
            AcademicSession.objects.filter(name=session).update(current=True)
            AcademicSession.objects.exclude(name=session).update(current=False)
            AcademicTerm.objects.filter(name=term).update(current=True)
            AcademicTerm.objects.exclude(name=term).update(current=False)
            messages.success(request, "Current session and term updated successfully.")

        return render(request, self.template_name, {"form": form})


def signup_view(request):
    ACCESS_CODE = '7BJW'
    LOCK_MINUTES = 30
    MAX_ATTEMPTS = 5

    # Initialize session counters
    attempts = int(request.session.get('signup_attempts', 0))
    lock_until_str = request.session.get('signup_lock_until')
    lock_until = None
    if lock_until_str:
        try:
            lock_until = timezone.datetime.fromisoformat(lock_until_str)
        except Exception:
            lock_until = None

    # Check lock status
    now = timezone.now()
    if lock_until and now < lock_until:
        remaining = (lock_until - now).seconds // 60 + 1
        messages.error(request, f'Too many invalid access code attempts. Try again in about {remaining} minute(s).')
        return render(request, 'registration/signup.html', {'form': UserCreationForm()})

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        access_code = (request.POST.get('access_code') or '').strip()

        # Validate access code first
        if access_code != ACCESS_CODE:
            attempts += 1
            request.session['signup_attempts'] = attempts
            if attempts >= MAX_ATTEMPTS:
                lock_until = now + timezone.timedelta(minutes=LOCK_MINUTES)
                request.session['signup_lock_until'] = lock_until.isoformat()
                messages.error(request, f'Too many invalid access code attempts. Locked for {LOCK_MINUTES} minute(s).')
            else:
                remaining = MAX_ATTEMPTS - attempts
                messages.error(request, f'Invalid access code. You have {remaining} attempt(s) left.')
            return render(request, 'registration/signup.html', {'form': form})

        # Access code correct; reset counters
        request.session['signup_attempts'] = 0
        request.session['signup_lock_until'] = None

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('corecode:home')
        else:
            # Do not count as rate-limit attempt; just show form errors
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'registration/signup.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Welcome back, {username}!')
                return redirect('corecode:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('corecode:login')


@login_required
def global_search(request):
    term = request.GET.get('q', '').strip()
    results = { 'students': [], 'staffs': [], 'invoices': [], 'classes': [] }
    if term:
        # Lazy imports to avoid circulars
        from apps.students.models import Student
        from apps.staffs.models import Staff
        from apps.finance.models import Invoice

        students = Student.objects.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(current_class__name__icontains=term)
        ).values('id', 'first_name', 'last_name')[:5]
        staffs = Staff.objects.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term)
        ).values('id', 'first_name', 'last_name')[:5]
        invoices = Invoice.objects.filter(
            Q(number__icontains=term) | Q(student__first_name__icontains=term) | Q(student__last_name__icontains=term)
        ).values('id', 'number')[:5]
        classes = StudentClass.objects.filter(Q(name__icontains=term)).values('id', 'name')[:5]

        results['students'] = [
            { 'id': s['id'], 'label': f"{s['first_name']} {s['last_name']}", 'url': f"/students/{s['id']}/" } for s in students
        ]
        results['staffs'] = [
            { 'id': s['id'], 'label': f"{s['first_name']} {s['last_name']}", 'url': f"/staffs/{s['id']}/" } for s in staffs
        ]
        results['invoices'] = [
            { 'id': i['id'], 'label': f"Invoice {i['number']}", 'url': f"/finance/invoice/{i['id']}/" } for i in invoices
        ]
        results['classes'] = [
            { 'id': c['id'], 'label': c['name'], 'url': f"/class/{c['id']}/" } for c in classes
        ]

    return JsonResponse(results)


@login_required
def notifications_feed(request):
    # Lazy imports
    from apps.finance.models import Invoice
    from attendance.models import AttendanceRegister

    unpaid = Invoice.objects.filter(status='Unpaid').count() if hasattr(Invoice, 'status') else 0
    pending_attendance = AttendanceRegister.objects.filter(is_open=True).count() if hasattr(AttendanceRegister, 'is_open') else 0

    feed = [
        { 'type': 'info', 'text': f'Unpaid invoices: {unpaid}', 'url': '/finance/invoice/list/' },
        { 'type': 'warning', 'text': f'Open attendance registers: {pending_attendance}', 'url': '/attendance/' },
    ]

    return JsonResponse({ 'items': feed })


@login_required
def send_notice(request):
    """Compose and send a notice to parents via Email and/or SMS, optionally filtered by class."""
    from django.utils import timezone
    from django.core.mail import EmailMessage
    from django.conf import settings
    from apps.students.models import Student

    def normalize_msisdn(num: str) -> str:
        if not num:
            return ''
        s = ''.join(ch for ch in str(num) if ch.isdigit() or ch == '+')
        return s

    def send_sms(msisdn: str, text: str) -> bool:
        # Placeholder for SMS gateway integration
        return bool(msisdn and text)

    context = {
        'classes': StudentClass.objects.all().order_by('name'),
        'now': timezone.now(),
    }

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        channels = request.POST.getlist('channels')  # ['email', 'sms']
        class_id = request.POST.get('class_id')

        if not subject or not message:
            messages.error(request, 'Subject and Message are required.')
            return render(request, 'notices/create.html', context)
        if not channels:
            messages.error(request, 'Select at least one delivery channel (Email or SMS).')
            return render(request, 'notices/create.html', context)

        qs = Student.objects.filter(current_status='active')
        if class_id:
            qs = qs.filter(current_class_id=class_id)

        emails = []
        phones = []
        for stu in qs.only('guardian_email', 'guardian_phone', 'parent_mobile_number'):
            if 'email' in channels and stu.guardian_email:
                emails.append(stu.guardian_email)
            if 'sms' in channels:
                num = stu.guardian_phone or stu.parent_mobile_number
                num = normalize_msisdn(num)
                if num:
                    phones.append(num)

        sent_email = 0
        sent_sms = 0
        if 'email' in channels and emails:
            unique_emails = list({e.lower(): e for e in emails if e}.values())
            chunk = 50
            for i in range(0, len(unique_emails), chunk):
                bcc = unique_emails[i:i+chunk]
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or None,
                    to=[],
                    bcc=bcc,
                )
                try:
                    email.send(fail_silently=False)
                    sent_email += len(bcc)
                except Exception:
                    pass

        if 'sms' in channels and phones:
            unique_phones = list({p: p for p in phones if p}.values())
            for p in unique_phones:
                try:
                    if send_sms(p, message):
                        sent_sms += 1
                except Exception:
                    continue

        messages.success(request, f"Notice sent. Emails: {sent_email}, SMS: {sent_sms}.")
        return render(request, 'notices/create.html', context)

    return render(request, 'notices/create.html', context)