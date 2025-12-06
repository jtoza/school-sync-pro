from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from apps.students.models import Student
from .forms import InvoiceItemFormset, InvoiceReceiptFormSet, Invoices
from .models import Invoice, InvoiceItem, Receipt
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json
import logging
from .lipana import LipanaMpesa

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('student', 'session', 'term', 'class_for')
        student = self.request.GET.get('student')
        status = self.request.GET.get('status')
        term = self.request.GET.get('term')
        session = self.request.GET.get('session')
        if student:
            qs = qs.filter(student__surname__icontains=student) | qs.filter(student__firstname__icontains=student)
        if status:
            qs = qs.filter(status=status)
        if term:
            qs = qs.filter(term_id=term)
        if session:
            qs = qs.filter(session_id=session)
        return qs.order_by('-last_modified')


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    fields = "__all__"
    success_url = "/finance/list"

    def get_context_data(self, **kwargs):
        context = super(InvoiceCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context["items"] = InvoiceItemFormset(
                self.request.POST, prefix="invoiceitem_set"
            )
        else:
            context["items"] = InvoiceItemFormset(prefix="invoiceitem_set")
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["items"]
        self.object = form.save()
        if self.object.id != None:
            if form.is_valid() and formset.is_valid():
                formset.instance = self.object
                formset.save()
                # Auto-close invoice if fully paid
                if self.object.balance() <= 0:
                    self.object.status = 'closed'
                    self.object.save(update_fields=['status'])
        return super().form_valid(form)


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        context["receipts"] = Receipt.objects.filter(invoice=self.object)
        context["items"] = InvoiceItem.objects.filter(invoice=self.object)
        context["summary"] = {
            'total_items': self.object.amount_payable(),
            'brought_forward': self.object.balance_from_previous_term,
            'total_payable': self.object.total_amount_payable(),
            'total_paid': self.object.total_amount_paid(),
            'balance': self.object.balance(),
            'status': self.object.status,
        }
        return context


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    fields = ["student", "session", "term", "class_for", "balance_from_previous_term"]

    def get_context_data(self, **kwargs):
        context = super(InvoiceUpdateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context["receipts"] = InvoiceReceiptFormSet(
                self.request.POST, instance=self.object
            )
            context["items"] = InvoiceItemFormset(
                self.request.POST, instance=self.object
            )
        else:
            context["receipts"] = InvoiceReceiptFormSet(instance=self.object)
            context["items"] = InvoiceItemFormset(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["receipts"]
        itemsformset = context["items"]
        if form.is_valid() and formset.is_valid() and itemsformset.is_valid():
            form.save()
            formset.save()
            itemsformset.save()
            invoice = self.object
            # Auto-close on full payment
            if invoice.balance() <= 0 and invoice.status != 'closed':
                invoice.status = 'closed'
                invoice.save(update_fields=['status'])
            # Auto-reopen when there is outstanding balance
            if invoice.balance() > 0 and invoice.status != 'active':
                invoice.status = 'active'
                invoice.save(update_fields=['status'])
        return super().form_valid(form)


class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    success_url = reverse_lazy("invoice-list")


class ReceiptCreateView(LoginRequiredMixin, CreateView):
    model = Receipt
    fields = ["amount_paid", "date_paid", "payment_method", "reference_code", "comment"]
    success_url = reverse_lazy("invoice-list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        invoice = Invoice.objects.get(pk=self.request.GET["invoice"])
        obj.invoice = invoice
        obj.received_by = self.request.user if self.request.user.is_authenticated else None
        if obj.amount_paid and obj.amount_paid > 0:
            obj.save()
            if invoice.balance() <= 0:
                invoice.status = 'closed'
                invoice.save(update_fields=['status'])
        return redirect("invoice-list")

    def get_context_data(self, **kwargs):
        context = super(ReceiptCreateView, self).get_context_data(**kwargs)
        invoice = Invoice.objects.get(pk=self.request.GET["invoice"])
        context["invoice"] = invoice
        return context


class ReceiptUpdateView(LoginRequiredMixin, UpdateView):
    model = Receipt
    fields = ["amount_paid", "date_paid", "comment"]
    success_url = reverse_lazy("invoice-list")


class ReceiptDeleteView(LoginRequiredMixin, DeleteView):
    model = Receipt
    success_url = reverse_lazy("invoice-list")


@login_required
def bulk_invoice(request):
    students = Student.objects.all().order_by('surname')[:100]
    return render(request, "finance/bulk_invoice.html", { 'students': students })


class MpesaPaymentView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "finance/mpesa_payment.html"
    context_object_name = "invoice"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        phone_number = request.POST.get('phone_number')
        amount = int(self.object.balance()) # Ensure integer for M-Pesa
        
        # Ensure phone number format (simple check)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # Callback URL
        callback_url = request.build_absolute_uri(reverse_lazy('mpesa-callback')) + f"?invoice_id={self.object.id}"
        # For local testing with localhost, this won't work for Lipana.
        # In production, this will be the correct URL.
        # If using a tunnel (ngrok), ensure ALLOWED_HOSTS includes it.
        
        account_reference = self.object.invoice_number
        transaction_desc = f"Green Bells Academy - Payment for {self.object.invoice_number}"

        lipana = LipanaMpesa()
        response = lipana.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            callback_url=callback_url
        )

        if response['success']:
            # Redirect to invoice detail with a success message
            # Ideally, we should show a "Processing" page or message
            return redirect(self.object.get_absolute_url())
        else:
            context = self.get_context_data(object=self.object)
            context['error'] = response['message']  # Fixed: removed duplicate line
            return render(request, self.template_name, context)


class PublicMpesaPaymentView(DetailView):
    model = Invoice
    template_name = "finance/mpesa_payment.html"
    context_object_name = "invoice"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        phone_number = request.POST.get('phone_number')
        amount = int(self.object.balance()) # Ensure integer for M-Pesa
        
        # Ensure phone number format (simple check)
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # Callback URL
        callback_url = request.build_absolute_uri(reverse_lazy('mpesa-callback')) + f"?invoice_id={self.object.id}"
        
        account_reference = self.object.invoice_number
        transaction_desc = f"Green Bells Academy - Payment for {self.object.invoice_number}"

        lipana = LipanaMpesa()
        response = lipana.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            callback_url=callback_url
        )

        if response['success']:
            # Since we don't have a specific success page for public, 
            # render the same template with success message.
            context = self.get_context_data(object=self.object)
            context['success'] = "Payment initiated successfully. Please check your phone."
            return render(request, self.template_name, context)
        else:
            context = self.get_context_data(object=self.object)
            context['error'] = response['message']
            return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            logger.info(f"M-Pesa Callback Data: {data}")
            
            # Parse Lipana/Daraja response
            # Try different response formats
            result_code = None
            checkout_request_id = None
            callback_metadata = None
            
            # Check for Lipana/Daraja format
            if 'ResultCode' in data:
                result_code = data.get('ResultCode')
                checkout_request_id = data.get('CheckoutRequestID')
                callback_metadata = data.get('CallbackMetadata', {})
            elif 'Body' in data:
                body = data.get('Body', {})
                stk_callback = body.get('stkCallback', {})
                result_code = stk_callback.get('ResultCode')
                checkout_request_id = stk_callback.get('CheckoutRequestID')
                callback_metadata = stk_callback.get('CallbackMetadata', {})
            
            if result_code == 0:
                # Payment Successful
                amount = 0
                receipt_number = ""
                phone_number = ""
                
                # Extract from callback metadata
                if isinstance(callback_metadata, dict) and 'Item' in callback_metadata:
                    items = callback_metadata.get('Item', [])
                    for item in items:
                        name = item.get('Name')
                        value = item.get('Value')
                        if name == 'Amount':
                            amount = value
                        elif name == 'MpesaReceiptNumber':
                            receipt_number = value
                        elif name == 'PhoneNumber':
                            phone_number = value
                
                # Get invoice_id from URL query parameters
                invoice_id = request.GET.get('invoice_id')
                if invoice_id:
                    try:
                        invoice = Invoice.objects.get(pk=invoice_id)
                        # Create Receipt
                        Receipt.objects.create(
                            invoice=invoice,
                            amount_paid=amount,
                            date_paid=timezone.now(),
                            payment_method='mpesa',
                            reference_code=receipt_number,
                            comment=f"Paid via M-Pesa {phone_number}"
                        )
                        logger.info(f"Receipt created for Invoice {invoice.invoice_number}")
                        
                        # Auto-close invoice if fully paid
                        if invoice.balance() <= 0:
                            invoice.status = 'closed'
                            invoice.save(update_fields=['status'])
                    except Invoice.DoesNotExist:
                        logger.error(f"Invoice {invoice_id} not found for callback")
                else:
                    logger.warning("No invoice_id in callback URL")

            else:
                error_msg = data.get('ResultDesc', 'Unknown error')
                logger.warning(f"M-Pesa payment failed: {error_msg}")

            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}")
            return JsonResponse({"status": "error"}, status=500)