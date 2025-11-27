from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View
from django.template.loader import get_template
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

from apps.corecode.models import StudentClass
from apps.students.models import Student
from apps.finance.models import Invoice, Receipt

from attendance.models import AttendanceEntry, AttendanceRegister
from .forms import CreateResults, EditResults
from .models import Result


@login_required
def student_performance(request):
    student = None
    labels = []
    totals = []
    reg = request.GET.get("reg")
    if reg:
        student = Student.objects.filter(registration_number=reg).first()
        if student:
            # Aggregate average total per (session, term)
            data = (
                Result.objects.filter(student=student)
                .values_list("session__name", "term__name")
                .order_by("session__name", "term__name")
            )
            # Build a stable unique ordered list
            seen = set()
            ordered_keys = []
            for s, t in data:
                key = f"{s} {t}"
                if key not in seen:
                    seen.add(key)
                    ordered_keys.append((s, t))
            from django.db.models import Avg, F, FloatField, ExpressionWrapper
            qs = (
                Result.objects.filter(student=student)
                .values("session__name", "term__name")
                .annotate(total=ExpressionWrapper(F("test_score") + F("exam_score"), output_field=FloatField()))
                .values("session__name", "term__name")
                .annotate(avg_total=Avg("total"))
                .order_by("session__name", "term__name")
            )
            agg = {(row["session__name"], row["term__name"]): row["avg_total"] for row in qs}
            labels = [f"{s} {t}" for s, t in ordered_keys]
            totals = [round(agg.get((s, t), 0), 2) for s, t in ordered_keys]
    context = {"student": student, "labels": labels, "totals": totals}
    return render(request, "result/student_performance.html", context)


@login_required
def create_result(request):
    students = Student.objects.all()
    if request.method == "POST":

        # after visiting the second page
        if "finish" in request.POST:
            form = CreateResults(request.POST)
            if form.is_valid():
                subjects = form.cleaned_data["subjects"]
                session = form.cleaned_data["session"]
                term = form.cleaned_data["term"]
                students = request.POST["students"]
                
                # Store selected students in session for edit_results
                request.session['selected_students'] = students.split(",")
                request.session['selected_subjects'] = [str(subj.id) for subj in subjects]
                request.session['results_session'] = str(session.id) if session else None
                request.session['results_term'] = str(term.id) if term else None
                
                results = []
                for student in students.split(","):
                    stu = Student.objects.get(pk=student)
                    if stu.current_class:
                        for subject in subjects:
                            check = Result.objects.filter(
                                session=session,
                                term=term,
                                current_class=stu.current_class,
                                subject=subject,
                                student=stu,
                            ).first()
                            if not check:
                                results.append(
                                    Result(
                                        session=session,
                                        term=term,
                                        current_class=stu.current_class,
                                        subject=subject,
                                        student=stu,
                                    )
                                )

                Result.objects.bulk_create(results)
                return redirect("edit-results")

        # after choosing students
        id_list = request.POST.getlist("students")
        if id_list:
            form = CreateResults(
                initial={
                    "session": request.current_session,
                    "term": request.current_term,
                }
            )
            studentlist = ",".join(id_list)
            return render(
                request,
                "result/create_result_page2.html",
                {"students": studentlist, "form": form, "count": len(id_list)},
            )
        else:
            messages.warning(request, "You didnt select any student.")
    return render(request, "result/create_result.html", {"students": students})


@login_required
def edit_results(request):
    if request.method == "POST":
        # Get the formset from POST data
        formset = EditResults(request.POST)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Results successfully updated")
            
            # Clear session data after successful save
            if 'selected_students' in request.session:
                del request.session['selected_students']
            if 'selected_subjects' in request.session:
                del request.session['selected_subjects']
                
            return redirect("edit-results")
    else:
        # Get selected students from session
        selected_student_ids = request.session.get('selected_students', [])
        selected_subject_ids = request.session.get('selected_subjects', [])
        session_id = request.session.get('results_session')
        term_id = request.session.get('results_term')
        
        # If no selected students in session, fall back to current session/term
        if not selected_student_ids:
            results = Result.objects.filter(
                session=request.current_session, 
                term=request.current_term
            )
        else:
            # Filter results to only show selected students and subjects
            results = Result.objects.filter(
                student__id__in=selected_student_ids,
                subject__id__in=selected_subject_ids,
                session_id=session_id or request.current_session.id,
                term_id=term_id or request.current_term.id
            )
        
        formset = EditResults(queryset=results)
    
    # Prepare data for template grouping
    selected_student_ids = request.session.get('selected_students', [])
    students_data = []
    
    if selected_student_ids:
        students = Student.objects.filter(id__in=selected_student_ids)
        for student in students:
            student_forms = [form for form in formset if form.instance.student_id == student.id]
            students_data.append({
                'student': student,
                'forms': student_forms,
                'results_count': len(student_forms)
            })
    
    context = {
        "formset": formset,
        "students_data": students_data,
        "selected_students_count": len(selected_student_ids),
        "subjects_count": len(request.session.get('selected_subjects', [])),
        "session": request.current_session,
        "term": request.current_term,
    }
    return render(request, "result/edit_results.html", context)


class ResultListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        results = Result.objects.filter(
            session=request.current_session, term=request.current_term
        )
        bulk = {}

        for result in results:
            test_total = 0
            exam_total = 0
            subjects = []
            for subject in results:
                if subject.student == result.student:
                    subjects.append(subject)
                    test_total += subject.test_score
                    exam_total += subject.exam_score

            bulk[result.student.id] = {
                "student": result.student,
                "subjects": subjects,
                "test_total": test_total,
                "exam_total": exam_total,
                "total_total": test_total + exam_total,
            }

        context = {"results": bulk}
        return render(request, "result/all_results.html", context)


@login_required
def report_card(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    session = request.current_session
    term = request.current_term
    results = Result.objects.filter(student=student, session=session, term=term).select_related('subject', 'current_class')
    teacher_comment = next((r.teacher_comment for r in results if r.teacher_comment), "")
    headteacher_comment = next((r.headteacher_comment for r in results if r.headteacher_comment), "")
    current_class = results.first().current_class if results.exists() else student.current_class

    regs = AttendanceRegister.objects.filter(
        session=session,
        term=term,
        student_class=current_class,
    )
    entries = AttendanceEntry.objects.filter(register__in=regs, student=student)
    present = entries.filter(status=AttendanceEntry.STATUS_PRESENT).count()
    absent = entries.filter(status=AttendanceEntry.STATUS_ABSENT).count()
    late = entries.filter(status=AttendanceEntry.STATUS_LATE).count()

    avg = sum(r.total_score() for r in results)/results.count() if results else 0

    # Attendance percentage
    total_att = present + absent + late
    attendance_pct = round((present / total_att) * 100, 1) if total_att else 0

    # Fee balance: sum per-invoice (invoice total/amount minus receipts or paid_amount)
    invoices = Invoice.objects.filter(student=student)
    if hasattr(Invoice, 'session'):
        invoices = invoices.filter(session=session)
    if hasattr(Invoice, 'term'):
        invoices = invoices.filter(term=term)

    fee_balance = 0.0
    for inv in invoices:
        base = getattr(inv, 'total', None)
        if base is None:
            base = getattr(inv, 'amount', 0) or 0
        base = float(base or 0)

        # Prefer explicit paid_amount/amount_paid on invoice if maintained
        paid_amount = getattr(inv, 'paid_amount', None)
        if paid_amount is None:
            paid_amount = getattr(inv, 'amount_paid', None)

        if paid_amount is not None:
            paid = float(paid_amount or 0)
        else:
            # Sum receipts tied to this invoice
            try:
                inv_receipts = Receipt.objects.filter(invoice=inv)
                paid = sum(float(getattr(rc, 'amount', 0) or 0) for rc in inv_receipts)
            except Exception:
                paid = 0.0

        due = max(base - paid, 0.0)
        fee_balance += due

    fee_balance = round(fee_balance, 2)

    context = {
        'student': student,
        'current_class': current_class,
        'session': session,
        'term': term,
        'results': results,
        'average_total': round(avg, 2),
        'attendance': {'present': present, 'absent': absent, 'late': late, 'percent': attendance_pct},
        'teacher_comment': teacher_comment,
        'headteacher_comment': headteacher_comment,
        'fee_balance': fee_balance,
    }
    return render(request, 'result/report_card.html', context)


@login_required
def render_to_pdf(request, template_src, context_dict={}):
    """
    Render HTML template to PDF using Playwright (Windows-friendly).
    Falls back to xhtml2pdf if Playwright is not available.
    """
    template = get_template(template_src)
    html_content = template.render(context=context_dict, request=request)
    
    # Try Playwright first (best for Windows, no system dependencies)
    try:
        from playwright.sync_api import sync_playwright
        
        result = BytesIO()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Build absolute base URL for resolving static and media files
            base_url = request.build_absolute_uri('/')
            
            # Set content with base URL for resolving relative paths
            page.set_content(html_content)
            
            # Generate PDF
            pdf_bytes = page.pdf(
                format='A4',
                margin={'top': '16mm', 'right': '14mm', 'bottom': '16mm', 'left': '14mm'},
                print_background=True
            )
            
            result.write(pdf_bytes)
            browser.close()
        
        result.seek(0)
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    except ImportError:
        # Playwright not installed, fallback to xhtml2pdf
        logger.warning('Playwright not available, falling back to xhtml2pdf')
        try:
            from xhtml2pdf import pisa
            from django.contrib.staticfiles import finders
            
            def link_callback(uri, rel):
                """Convert URIs to absolute system paths for static/media files"""
                # Handle static files
                if settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
                    # Remove the static URL prefix
                    static_path = uri.replace(settings.STATIC_URL, '').lstrip('/')
                    
                    # Try to find the file using Django's staticfiles finder
                    found_path = finders.find(static_path)
                    if found_path and os.path.exists(found_path):
                        return found_path
                    
                    # Fallback: try STATIC_ROOT
                    if settings.STATIC_ROOT:
                        path = os.path.join(settings.STATIC_ROOT, static_path)
                        if os.path.exists(path):
                            return path
                    
                    # Fallback: try STATICFILES_DIRS
                    if settings.STATICFILES_DIRS:
                        for static_dir in settings.STATICFILES_DIRS:
                            path = os.path.join(static_dir, static_path)
                            if os.path.exists(path):
                                return path
                    
                    logger.warning(f'Static file not found: {uri}')
                    return uri
                
                # Handle media files
                if settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
                    media_path = uri.replace(settings.MEDIA_URL, '').lstrip('/')
                    path = os.path.join(settings.MEDIA_ROOT, media_path)
                    if os.path.exists(path):
                        return path
                    logger.warning(f'Media file not found: {uri}')
                    return uri
                
                # Return original URI for absolute URLs or other cases
                return uri
            
            result = BytesIO()
            pdf = pisa.pisaDocument(
                BytesIO(html_content.encode('UTF-8')), 
                result, 
                encoding='UTF-8', 
                link_callback=link_callback
            )
            
            if not pdf.err:
                result.seek(0)
                return HttpResponse(result.getvalue(), content_type='application/pdf')
            else:
                logger.error(f'xhtml2pdf error: {pdf.err}')
                return None
                
        except ImportError:
            logger.error('Neither Playwright nor xhtml2pdf is available')
            return None
    
    except Exception as e:
        logger.error(f'PDF generation error: {str(e)}', exc_info=True)
        return None


@login_required
def report_card_pdf(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    session = request.current_session
    term = request.current_term
    # Assemble the same context as HTML view
    results = Result.objects.filter(student=student, session=session, term=term).select_related('subject', 'current_class')
    teacher_comment = next((r.teacher_comment for r in results if r.teacher_comment), "")
    headteacher_comment = next((r.headteacher_comment for r in results if r.headteacher_comment), "")
    current_class = results.first().current_class if results.exists() else student.current_class

    regs = AttendanceRegister.objects.filter(session=session, term=term, student_class=current_class)
    entries = AttendanceEntry.objects.filter(register__in=regs, student=student)
    present = entries.filter(status=AttendanceEntry.STATUS_PRESENT).count()
    absent = entries.filter(status=AttendanceEntry.STATUS_ABSENT).count()
    late = entries.filter(status=AttendanceEntry.STATUS_LATE).count()
    avg = sum(r.total_score() for r in results)/results.count() if results else 0

    total_att = present + absent + late
    attendance_pct = round((present / total_att) * 100, 1) if total_att else 0

    invoices = Invoice.objects.filter(student=student)
    if hasattr(Invoice, 'session'):
        invoices = invoices.filter(session=session)
    if hasattr(Invoice, 'term'):
        invoices = invoices.filter(term=term)

    fee_balance = 0.0
    for inv in invoices:
        base = getattr(inv, 'total', None)
        if base is None:
            base = getattr(inv, 'amount', 0) or 0
        base = float(base or 0)

        paid_amount = getattr(inv, 'paid_amount', None)
        if paid_amount is None:
            paid_amount = getattr(inv, 'amount_paid', None)

        if paid_amount is not None:
            paid = float(paid_amount or 0)
        else:
            try:
                inv_receipts = Receipt.objects.filter(invoice=inv)
                paid = sum(float(getattr(rc, 'amount', 0) or 0) for rc in inv_receipts)
            except Exception:
                paid = 0.0

        due = max(base - paid, 0.0)
        fee_balance += due

    fee_balance = round(fee_balance, 2)

    context = {
        'student': student,
        'current_class': current_class,
        'session': session,
        'term': term,
        'results': results,
        'average_total': round(avg, 2),
        'attendance': {'present': present, 'absent': absent, 'late': late, 'percent': attendance_pct},
        'teacher_comment': teacher_comment,
        'headteacher_comment': headteacher_comment,
        'pdf_mode': True,
        'fee_balance': fee_balance,
    }

    response = render_to_pdf(request, 'result/report_card_pdf.html', context)
    if response is None:
        messages.error(request, 'Failed to generate PDF report card')
        return redirect('report-card', student_id=student_id)
    filename = f"report_card_{student.registration_number}_{session}_{term}.pdf".replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def class_report_cards_pdf(request, class_id):
    student_class = get_object_or_404(StudentClass, pk=class_id)
    session = request.current_session
    term = request.current_term
    students = Student.objects.filter(current_class=student_class, current_status='active')

    pdf_buffers = []
    for student in students:
        results = Result.objects.filter(student=student, session=session, term=term).select_related('subject', 'current_class')
        teacher_comment = next((r.teacher_comment for r in results if r.teacher_comment), "")
        headteacher_comment = next((r.headteacher_comment for r in results if r.headteacher_comment), "")
        current_class = results.first().current_class if results.exists() else student.current_class

        regs = AttendanceRegister.objects.filter(session=session, term=term, student_class=current_class)
        entries = AttendanceEntry.objects.filter(register__in=regs, student=student)
        present = entries.filter(status=AttendanceEntry.STATUS_PRESENT).count()
        absent = entries.filter(status=AttendanceEntry.STATUS_ABSENT).count()
        late = entries.filter(status=AttendanceEntry.STATUS_LATE).count()
        avg = sum(r.total_score() for r in results)/results.count() if results else 0

        context = {
            'student': student,
            'current_class': current_class,
            'session': session,
            'term': term,
            'results': results,
            'average_total': round(avg, 2),
            'attendance': {'present': present, 'absent': absent, 'late': late},
            'teacher_comment': teacher_comment,
            'headteacher_comment': headteacher_comment,
            'pdf_mode': True,
        }
        # Render each student's PDF HTML
        template = get_template('result/report_card_pdf.html')
        html_content = template.render(context=context, request=request)
        
        # Use render_to_pdf helper for consistency
        pdf_response = render_to_pdf(request, 'result/report_card_pdf.html', context)
        if pdf_response:
            pdf_buffers.append(pdf_response.content)
        else:
            logger.warning(f'Failed to generate PDF for student {student.id}, skipping...')
            continue

    # Merge PDFs into a single file (simple concatenation via PyPDF2 if available)
    try:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        for content in pdf_buffers:
            bio = BytesIO(content)
            merger.append(bio)
        out = BytesIO()
        merger.write(out)
        merger.close()
        resp = HttpResponse(out.getvalue(), content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="class_report_cards_{student_class.name}_{session}_{term}.pdf"'.replace(' ', '_')
        return resp
    except Exception:
        # Fallback: zip files
        import zipfile
        out = BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, (stu, content) in enumerate(zip(students, pdf_buffers), start=1):
                zf.writestr(f"{stu.registration_number or idx}_{stu.last_name}.pdf", content)
        resp = HttpResponse(out.getvalue(), content_type='application/zip')
        resp['Content-Disposition'] = f'attachment; filename="class_report_cards_{student_class.name}_{session}_{term}.zip"'.replace(' ', '_')
        return resp


@login_required
def class_report_sheet(request, class_id):
    student_class = get_object_or_404(StudentClass, pk=class_id)
    session = request.current_session
    term = request.current_term
    students = Student.objects.filter(current_class=student_class, current_status='active')

    rows = []
    regs = AttendanceRegister.objects.filter(session=session, term=term, student_class=student_class)
    for stu in students:
        results = Result.objects.filter(student=stu, session=session, term=term)
        avg = round(sum(r.total_score() for r in results)/results.count(), 2) if results else 0
        entries = AttendanceEntry.objects.filter(register__in=regs, student=stu)
        present = entries.filter(status=AttendanceEntry.STATUS_PRESENT).count()
        absent = entries.filter(status=AttendanceEntry.STATUS_ABSENT).count()
        late = entries.filter(status=AttendanceEntry.STATUS_LATE).count()
        rows.append({
            'student': stu,
            'average_total': avg,
            'attendance': {'present': present, 'absent': absent, 'late': late}
        })

    context = {
        'student_class': student_class,
        'session': session,
        'term': term,
        'rows': rows,
    }
    return render(request, 'result/class_report_sheet.html', context)