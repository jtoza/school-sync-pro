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
    results_access,
    send_result_sms_view,
    send_result_sms_action,
    send_individual_result_sms,
)
from .views_analytics import (
    analytics_dashboard,
    bulk_upload_results,
    download_bulk_template,
)

urlpatterns = [
    path("create/", create_result, name="create-result"),
    path("edit-results/", edit_results, name="edit-results"),
    path("access/", results_access, name="results-access"),
    path("view/all", ResultListView.as_view(), name="view-results"),
    path("performance/", student_performance, name="student-performance"),
    path("report-card/<int:student_id>/", report_card, name="report-card"),
    path("report-card/<int:student_id>/pdf/", report_card_pdf, name="report-card-pdf"),
    path("class-sheet/<int:class_id>/", class_report_sheet, name="class-report-sheet"),
    path("class-report/<int:class_id>/pdf/", class_report_cards_pdf, name="class-report-pdf"),
    # Analytics and bulk upload URLs
    path("analytics/", analytics_dashboard, name="analytics-dashboard"),
    path("bulk-upload/", bulk_upload_results, name="bulk-upload-results"),
    path("bulk-upload/template/", download_bulk_template, name="bulk-template"),
    # SMS notification URLs
    path("send-sms/", send_result_sms_view, name="send-result-sms"),
    path("send-sms/action/", send_result_sms_action, name="send-result-sms-action"),
    path("result/<int:pk>/send-sms/", send_individual_result_sms, name="send-individual-sms"),
]
