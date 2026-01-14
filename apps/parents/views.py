from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Sum, Avg

from apps.students.models import Student
from apps.finance.models import Invoice, InvoiceItem, Receipt
from apps.result.models import Result


@require_http_methods(["GET", "POST"])
def parent_access(request):
    """
    Step 1: Ask for Student Registration Number (Student ID)
    Step 2: On submit, show a summary page with fees and performance.
    """
    if request.method == "POST":
        reg_no = (request.POST.get("registration_number") or "").strip()
        if not reg_no:
            messages.error(request, "Please enter a Student ID (registration number).")
            return render(request, "parents/parent_access.html")

        try:
            student = Student.objects.get(registration_number__iexact=reg_no)
        except Student.DoesNotExist:
            messages.error(request, "Student not found. Check the Student ID and try again.")
            return render(request, "parents/parent_access.html")

        # Finance summary
        invoices = (
            Invoice.objects.filter(student=student)
            .select_related("session", "term", "class_for")
            .order_by("-session__name", "-term__name")
        )
        total_payable = 0
        total_paid = 0
        balance = 0
        latest_invoice = None
        if invoices:
            latest_invoice = invoices.first()
            total_payable = sum(inv.total_amount_payable() for inv in invoices)
            total_paid = sum(inv.total_amount_paid() for inv in invoices)
            balance = total_payable - total_paid

        # Performance summary
        results = (
            Result.objects.filter(student=student)
            .select_related("session", "term", "current_class", "subject")
            .order_by("-session__name", "-term__name", "subject__name")
        )
        # Aggregate performance per session/term
        performance = {}
        for r in results:
            key = f"{getattr(r.session, 'name', '')} - {getattr(r.term, 'name', '')}"
            if key not in performance:
                performance[key] = {
                    "total": 0,
                    "count": 0,
                    "avg": 0,
                    "subjects": [],
                }
            total_score = r.total_score() if hasattr(r, "total_score") else (r.test_score + r.exam_score)
            performance[key]["total"] += total_score
            performance[key]["count"] += 1
            performance[key]["subjects"].append({
                "subject": getattr(r.subject, "name", ""),
                "ca": r.test_score,
                "exam": r.exam_score,
                "total": total_score,
                "grade": r.grade() if hasattr(r, "grade") else "",
            })

        for key, val in performance.items():
            if val["count"]:
                val["avg"] = round(val["total"] / val["count"], 2)

        context = {
            "student": student,
            "latest_invoice": latest_invoice,
            "invoices": invoices[:5],  # show last 5
            "fees_summary": {
                "total_payable": total_payable,
                "total_paid": total_paid,
                "balance": balance,
            },
            "performance": performance,
        }
        return render(request, "parents/parent_access_result.html", context)

    # GET request -> show form
    return render(request, "parents/parent_access.html")
