import uuid
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.corecode.models import AcademicSession, AcademicTerm, StudentClass
from apps.students.models import Student


class Invoice(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    class_for = models.ForeignKey(StudentClass, on_delete=models.CASCADE)
    balance_from_previous_term = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("closed", "Closed")],
        default="active",
    )

    # Human-friendly invoice number and currency
    invoice_number = models.CharField(max_length=30, blank=True, null=True, editable=False)
    currency = models.CharField(max_length=5, default='NGN')

    # SYNC FIELDS
    sync_id = models.UUIDField(unique=True, blank=True, null=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[('synced', 'Synced'), ('pending', 'Pending'), ('conflict', 'Conflict')],
        default='synced'
    )
    last_modified = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["student", "term"]

    def save(self, *args, **kwargs):
        # Generate sync_id if it doesn't exist
        if not self.sync_id:
            self.sync_id = uuid.uuid4()
        # Generate invoice number if missing
        if not self.invoice_number:
            today = timezone.now().strftime('%Y%m%d')
            prefix = f"INV-{today}-"
            # Build a monotonic sequence per day
            seq = Invoice.objects.filter(invoice_number__startswith=prefix).count() + 1
            candidate = f"{prefix}{seq:06d}"
            # In rare case of collision, increment until unique
            while Invoice.objects.filter(invoice_number=candidate).exists():
                seq += 1
                candidate = f"{prefix}{seq:06d}"
            self.invoice_number = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number or 'INV'} - {self.student}"

    def balance(self):
        payable = self.total_amount_payable()
        paid = self.total_amount_paid()
        return payable - paid

    def amount_payable(self):
        items = InvoiceItem.objects.filter(invoice=self)
        total = 0
        for item in items:
            total += item.amount
        return total

    def total_amount_payable(self):
        return self.balance_from_previous_term + self.amount_payable()

    def total_amount_paid(self):
        receipts = Receipt.objects.filter(invoice=self)
        amount = 0
        for receipt in receipts:
            amount += receipt.amount_paid
        return amount

    def get_absolute_url(self):
        return reverse("invoice-detail", kwargs={"pk": self.pk})


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.IntegerField()

    # SYNC FIELDS
    sync_id = models.UUIDField(unique=True, blank=True, null=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[('synced', 'Synced'), ('pending', 'Pending'), ('conflict', 'Conflict')],
        default='synced'
    )
    last_modified = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Generate sync_id if it doesn't exist
        if not self.sync_id:
            self.sync_id = uuid.uuid4()
        super().save(*args, **kwargs)


class Receipt(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount_paid = models.IntegerField()
    date_paid = models.DateField(default=timezone.now)
    comment = models.CharField(max_length=200, blank=True)

    # Human-friendly receipt number and payment metadata
    receipt_number = models.CharField(max_length=30, blank=True, null=True, editable=False)
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
        ('pos', 'POS'),
        ('other', 'Other'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    reference_code = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='receipts_received')

    # SYNC FIELDS
    sync_id = models.UUIDField(unique=True, blank=True, null=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[('synced', 'Synced'), ('pending', 'Pending'), ('conflict', 'Conflict')],
        default='synced'
    )
    last_modified = models.DateTimeField(auto_now=True)
    device_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Generate sync_id if it doesn't exist
        if not self.sync_id:
            self.sync_id = uuid.uuid4()
        # Generate receipt number if missing
        if not self.receipt_number:
            today = timezone.now().strftime('%Y%m%d')
            prefix = f"RCPT-{today}-"
            seq = Receipt.objects.filter(receipt_number__startswith=prefix).count() + 1
            candidate = f"{prefix}{seq:06d}"
            while Receipt.objects.filter(receipt_number=candidate).exists():
                seq += 1
                candidate = f"{prefix}{seq:06d}"
            self.receipt_number = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number or 'Receipt'} on {self.date_paid}"
