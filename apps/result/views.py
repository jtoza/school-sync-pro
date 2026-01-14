from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View
from django.template.loader import get_template
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
import os
import logging

logger = logging.getLogger(__name__)

from apps.corecode.models import StudentClass
from apps.students.models import Student
from apps.finance.models import Invoice, Receipt

from attendance.models import AttendanceEntry, AttendanceRegister
from .forms import CreateResults, EditResults
from .models import Result
from .utils_pdf import generate_pdf_from_html_content


@login_required
def results_access(request):
    """Search results by Student registration number and display only that student's results."""
    if request.method == 'POST':
        reg_no = (request.POST.get('registration_number') or '').strip()
        if not reg_no:
            messages.error(request, 'Please enter a Student ID (registration number).')
            return render(request, 'result/results_access.html')

        student = Student.objects.filter(registration_number__iexact=reg_no).first()
        if not student:
            messages.error(request, 'Student not found. Check the Student ID and try again.')
            return render(request, 'result/results_access.html')

        # Fetch results grouped by session/term, with subject breakdown
        results = (
            Result.objects.filter(student=student)
            .select_related('session', 'term', 'current_class', 'subject')
            .order_by('session__name', 'term__name', 'subject__name')
        )
        performance = {}
        for r in results:
            key = f"{getattr(r.session, 'name', '')} - {getattr(r.term, 'name', '')}"
            perf = performance.setdefault(key, { 'subjects': [], 'total': 0, 'count': 0, 'avg': 0 })
            total_score = r.total_score() if hasattr(r, 'total_score') else (r.test_score + r.exam_score)
            perf['subjects'].append({
                'subject': getattr(r.subject, 'name', ''),
                'ca': r.test_score,
                'exam': r.exam_score,
                'total': total_score,
                'grade': r.grade() if hasattr(r, 'grade') else '',
            })
            perf['total'] += total_score
            perf['count'] += 1
        for k, v in performance.items():
            if v['count']:
                v['avg'] = round(v['total'] / v['count'], 2)

        context = {
            'student': student,
            'performance': performance,
        }
        return render(request, 'result/results_student.html', context)

    # GET request -> show form
    return render(request, 'result/results_access.html')


@login_required
def student_performance(request):
    """
    Show student's performance trend across session/term with insights.
    Returns labels, totals series, and analytics like best/worst term, streak and overall average.
    """
    student = None
    reg = (request.GET.get("reg") or "").strip()

    labels = []
    totals = []
    ca_averages = []
    exam_averages = []
    gpas = []

    insights = {
        "overall_average": 0.0,
        "best": None,   # {label, value}
        "worst": None,  # {label, value}
        "trend": "flat",  # up|down|flat
        "streak": 0,
    }

    if reg:
        student = Student.objects.filter(registration_number__iexact=reg).first()
        if student:
            from django.db.models import Avg, F, FloatField, ExpressionWrapper

            # Build ordered unique (session, term) keys based on available results
            data = (
                Result.objects.filter(student=student)
                .values_list("session__name", "term__name")
                .order_by("session__name", "term__name")
            )
            seen = set()
            ordered_keys = []
            for s, t in data:
                key = f"{s} {t}"
                if key not in seen:
                    seen.add(key)
                    ordered_keys.append((s, t))

            if ordered_keys:
                # Compute CA avg, Exam avg and Total avg per (session, term) without nested aggregates
                agg_qs = (
                    Result.objects.filter(student=student)
                    .values("session__name", "term__name")
                    .annotate(
                        ca_avg=Avg("test_score"),
                        exam_avg=Avg("exam_score"),
                        avg_total=Avg(F("test_score") + F("exam_score")),
                    )
                    .order_by("session__name", "term__name")
                )
                agg_map = {
                    (row["session__name"], row["term__name"]): (
                        float(row.get("ca_avg") or 0),
                        float(row.get("exam_avg") or 0),
                        float(row.get("avg_total") or 0),
                    )
                    for row in agg_qs
                }

                # Labels and series
                labels = [f"{s} {t}" for (s, t) in ordered_keys]
                for key in ordered_keys:
                    ca, ex, tot = agg_map.get(key, (0.0, 0.0, 0.0))
                    ca_averages.append(round(ca, 2))
                    exam_averages.append(round(ex, 2))
                    totals.append(round(tot, 2))

                # Optional GPA per term if function available
                # We need session and term objects; fetch by names to avoid extra joins
                try:
                    from apps.corecode.models import AcademicSession, AcademicTerm
                    for (s_name, t_name) in ordered_keys:
                        sess = AcademicSession.objects.filter(name=s_name).first()
                        term = AcademicTerm.objects.filter(name=t_name).first()
                        if sess and term:
                            gpa_val = Result.get_student_gpa(student, sess, term)
                            gpas.append(round(float(gpa_val or 0), 2))
                        else:
                            gpas.append(0.0)
                except Exception:
                    # If GPA calc not available, keep zeros
                    gpas = [0.0 for _ in ordered_keys]

                # Insights
                if totals:
                    # overall average
                    insights["overall_average"] = round(sum(totals) / len(totals), 2)

                    # best/worst
                    best_idx = max(range(len(totals)), key=lambda i: totals[i])
                    worst_idx = min(range(len(totals)), key=lambda i: totals[i])
                    insights["best"] = {"label": labels[best_idx], "value": totals[best_idx]}
                    insights["worst"] = {"label": labels[worst_idx], "value": totals[worst_idx]}

                    # trend based on last two points
                    if len(totals) >= 2:
                        if totals[-1] > totals[-2]:
                            insights["trend"] = "up"
                        elif totals[-1] < totals[-2]:
                            insights["trend"] = "down"
                        else:
                            insights["trend"] = "flat"

                        # streak (consecutive up or down moves from the end)
                        direction = 1 if totals[-1] > totals[-2] else (-1 if totals[-1] < totals[-2] else 0)
                        streak = 1 if direction != 0 else 0
                        for i in range(len(totals) - 2, 0, -1):
                            diff = totals[i] - totals[i - 1]
                            if diff == 0:
                                break
                            d = 1 if diff > 0 else -1
                            if d == direction:
                                streak += 1
                            else:
                                break
                        insights["streak"] = streak

    context = {
        "student": student,
        "labels": labels,
        "totals": totals,
        "ca_averages": ca_averages,
        "exam_averages": exam_averages,
        "gpas": gpas,
        "insights": insights,
        "reg": reg,
    }
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
        # Rebuild the same queryset used when rendering the formset
        selected_student_ids = request.session.get('selected_students', [])
        selected_subject_ids = request.session.get('selected_subjects', [])
        session_id = request.session.get('results_session') or getattr(request.current_session, 'id', None)
        term_id = request.session.get('results_term') or getattr(request.current_term, 'id', None)

        if selected_student_ids:
            results = Result.objects.filter(
                student__id__in=selected_student_ids,
                subject__id__in=selected_subject_ids if selected_subject_ids else Result.objects.values_list('subject_id', flat=True),
                session_id=session_id,
                term_id=term_id,
            )
        else:
            results = Result.objects.filter(
                session=request.current_session,
                term=request.current_term,
            )

        # Bind POST to the exact queryset so submitted forms map correctly
        formset = EditResults(request.POST, queryset=results)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Results successfully updated")
            
            # Clear session data after successful save
            for key in ('selected_students', 'selected_subjects', 'results_session', 'results_term'):
                if key in request.session:
                    del request.session[key]
            
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
    
    # Calculate GPA and Position
    from .utils import calculate_gpa, get_gpa_class, get_student_position
    gpa = calculate_gpa(results) if results.exists() else 0.0
    gpa_class = get_gpa_class(gpa)
    position_data = get_student_position(student, session, term)

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
        'gpa': gpa,
        'gpa_class': gpa_class,
        'position_data': position_data,
    }
    return render(request, 'result/report_card.html', context)


@login_required
def render_to_pdf(request, template_src, context_dict={}):
    """
    Render HTML template to PDF using our wrapper.
    Falls back to xhtml2pdf if Playwright is not available.
    """
    html = render_to_string(template_src, context_dict)
    output_path = f"/tmp/temp_report.pdf"

    try:
        # Generate PDF using Playwright wrapper
        generate_pdf_from_html_content(html, output_path)

        with open(output_path, "rb") as f:
            return HttpResponse(f.read(), content_type="application/pdf")

    except Exception as e:
        # Fallback to xhtml2pdf if Playwright fails
        logger.warning(f'Playwright PDF generation failed: {str(e)}')
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
                BytesIO(html.encode('UTF-8')), 
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


# SMS Result Notification Views
@login_required
def send_result_sms_view(request):
    """Display form for sending result SMS"""
    from apps.corecode.models import AcademicSession, AcademicTerm
    
    sessions = AcademicSession.objects.all()
    terms = AcademicTerm.objects.all()
    classes = StudentClass.objects.all()
    
    context = {
        'sessions': sessions,
        'terms': terms,
        'classes': classes,
        'current_session': request.current_session,
        'current_term': request.current_term,
    }
    return render(request, 'result/send_sms.html', context)


@login_required
def send_result_sms_action(request):
    """Process SMS sending for selected students"""
    from apps.corecode.models import AcademicSession, AcademicTerm
    from .sms import send_bulk_result_sms
    
    if request.method != 'POST':
        return redirect('send-result-sms')
    
    session_id = request.POST.get('session')
    term_id = request.POST.get('term')
    class_id = request.POST.get('student_class')
    student_ids = request.POST.getlist('students')
    
    if not session_id or not term_id:
        messages.error(request, 'Please select session and term')
        return redirect('send-result-sms')
    
    session = get_object_or_404(AcademicSession, pk=session_id)
    term = get_object_or_404(AcademicTerm, pk=term_id)
    
    # Get students
    if student_ids:
        students = Student.objects.filter(pk__in=student_ids)
    elif class_id:
        students = Student.objects.filter(current_class_id=class_id, current_status='active')
    else:
        messages.error(request, 'Please select students or a class')
        return redirect('send-result-sms')
    
    if not students.exists():
        messages.error(request, 'No students found')
        return redirect('send-result-sms')
    
    # Send SMS
    result = send_bulk_result_sms(students, session, term)
    
    if result['success']:
        messages.success(
            request,
            f"SMS sent successfully to {result['sent']} student(s). "
            f"{result['failed']} failed."
        )
    else:
        messages.error(request, f"Failed to send SMS. {result['failed']} failed.")
    
    # Show details
    for detail in result['details']:
        if not detail['success']:
            messages.warning(
                request,
                f"{detail['student']}: {detail['error']}"
            )
    
    return redirect('send-result-sms')


@login_required
def send_individual_result_sms(request, pk):
    """Send SMS for a single student's result"""
    from .sms import send_result_sms
    
    result_obj = get_object_or_404(Result, pk=pk)
    student = result_obj.student
    session = result_obj.session
    term = result_obj.term
    
    # Send SMS
    result = send_result_sms(student, session, term)
    
    if result['success']:
        messages.success(request, f"SMS sent to {student.get_short_name()}'s parent")
    else:
        messages.error(request, f"Failed to send SMS: {result['message']}")
    
    return redirect(request.META.get('HTTP_REFERER', 'result-list'))