from django.urls import path

from .views import (
    ResultListView,
    create_result,
    edit_results,
    student_performance,
    report_card,
    class_report_sheet,
    report_card_pdf,
    class_report_cards_pdf,
)

urlpatterns = [
    path("create/", create_result, name="create-result"),
    path("edit-results/", edit_results, name="edit-results"),
    path("view/all", ResultListView.as_view(), name="view-results"),
    path("performance/", student_performance, name="student-performance"),
    path("report-card/<int:student_id>/", report_card, name="report-card"),
    path("report-card/<int:student_id>/pdf/", report_card_pdf, name="report-card-pdf"),
    path("class-sheet/<int:class_id>/", class_report_sheet, name="class-report-sheet"),
    path("class-report/<int:class_id>/pdf/", class_report_cards_pdf, name="class-report-pdf"),
]
