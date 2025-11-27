from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib import messages
from apps.students.models import Student
from apps.finance.models import Invoice, Receipt

class ParentPortalHomeView(TemplateView):
    """Landing page for parent portal with student ID lookup"""
    template_name = 'parents/portal_home.html'

class StudentFeeLookupView(TemplateView):
    """View to handle student ID lookup and display fee details"""
    template_name = 'parents/fee_lookup.html'
    
    def post(self, request, *args, **kwargs):
        student_id = request.POST.get('student_id', '').strip()
        
        if not student_id:
            messages.error(request, 'Please enter a student ID or registration number.')
            return self.get(request, *args, **kwargs)
        
        # Try to find student by registration number or ID
        try:
            # First try by registration number
            student = Student.objects.filter(registration_number=student_id).first()
            
            # If not found, try by ID
            if not student:
                try:
                    student = Student.objects.filter(id=int(student_id)).first()
                except ValueError:
                    pass
            
            if student:
                return redirect('student-fee-detail-public', student_id=student.id)
            else:
                messages.error(request, f'No student found with ID: {student_id}')
                return redirect('parent-portal-home')
                
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            return redirect('parent-portal-home')

class StudentFeeDetailPublicView(DetailView):
    """Public view to display student fee details without authentication"""
    model = Student
    template_name = 'parents/student_fee_detail_public.html'
    pk_url_kwarg = 'student_id'
    context_object_name = 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        invoices = Invoice.objects.filter(student=student).order_by('-session', '-term')
        
        total_payable = 0
        total_paid = 0
        all_receipts = []

        for invoice in invoices:
            total_payable += invoice.total_amount_payable()
            total_paid += invoice.total_amount_paid()
            receipts = Receipt.objects.filter(invoice=invoice).order_by('-date_paid')
            for receipt in receipts:
                all_receipts.append(receipt)
        
        # Get student results/performance
        from apps.result.models import Result
        results = Result.objects.filter(student=student).order_by('-session', '-term')
        
        context['invoices'] = invoices
        context['receipts'] = all_receipts
        context['total_outstanding'] = total_payable - total_paid
        context['total_payable'] = total_payable
        context['total_paid'] = total_paid
        context['results'] = results
        return context

class DownloadReceiptView(TemplateView):
    template_name = 'parents/receipt_download.html'
    
    def get(self, request, *args, **kwargs):
        messages.info(request, 'PDF download feature coming soon!')
        return redirect('parent-portal-home')

class StudentStatementView(TemplateView):
    template_name = 'parents/statement.html'
    
    def get(self, request, *args, **kwargs):
        messages.info(request, 'Statement generation feature coming soon!')
        return redirect('parent-portal-home')
