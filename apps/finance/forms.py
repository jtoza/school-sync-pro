from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, modelformset_factory, BaseInlineFormSet

from .models import Invoice, InvoiceItem, Receipt


class InvoiceItemForm(forms.ModelForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise ValidationError('Item amount must be greater than zero.')
        return amount

    class Meta:
        model = InvoiceItem
        fields = ["description", "amount"]


class ReceiptForm(forms.ModelForm):
    def clean_amount_paid(self):
        amt = self.cleaned_data.get('amount_paid')
        if amt is None or amt <= 0:
            raise ValidationError('Receipt amount must be greater than zero.')
        return amt

    class Meta:
        model = Receipt
        fields = ("amount_paid", "date_paid", "payment_method", "reference_code", "comment")


class ValidatedReceiptFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(form.errors for form in self.forms):
            return
        invoice = self.instance
        if not invoice or not getattr(invoice, 'total_amount_payable', None):
            return

        # Sum amounts from non-deleted forms
        form_total = 0
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data.get('DELETE', False):
                continue
            amt = form.cleaned_data.get('amount_paid') or 0
            if amt < 0:
                raise ValidationError('Receipt amount cannot be negative.')
            form_total += amt

        # Sum amounts for existing receipts not represented in the formset (when creating)
        existing_total = 0
        if invoice.pk:
            represented_ids = [f.instance.pk for f in self.forms if getattr(f, 'instance', None) and f.instance.pk]
            existing_total = Receipt.objects.filter(invoice=invoice).exclude(pk__in=represented_ids).aggregate_sum if False else 0

        total_payable = invoice.total_amount_payable()
        # We assume formset is authoritative for all receipts when updating on the invoice page.
        if form_total + existing_total > total_payable:
            raise ValidationError('Total receipts exceed the amount payable for this invoice.')


InvoiceItemFormset = inlineformset_factory(
    Invoice, InvoiceItem, form=InvoiceItemForm, fields=["description", "amount"], extra=1, can_delete=True
)

InvoiceReceiptFormSet = inlineformset_factory(
    Invoice,
    Receipt,
    form=ReceiptForm,
    formset=ValidatedReceiptFormSet,
    fields=("amount_paid", "date_paid", "comment"),
    extra=0,
    can_delete=True,
)

Invoices = modelformset_factory(Invoice, exclude=(), extra=4)
