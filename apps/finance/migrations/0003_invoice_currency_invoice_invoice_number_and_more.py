# finance/migrations/0003_invoice_currency_invoice_invoice_number_and_more.py
# Generated manually to safely add new fields without breaking migration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_invoice_device_id_invoice_last_modified_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add currency field to Invoice
        migrations.AddField(
            model_name='invoice',
            name='currency',
            field=models.CharField(default='NGN', max_length=5),
        ),

        # Add invoice_number field WITHOUT unique initially
        migrations.AddField(
            model_name='invoice',
            name='invoice_number',
            field=models.CharField(blank=True, editable=False, max_length=30),
        ),

        # Add payment_method field to Receipt
        migrations.AddField(
            model_name='receipt',
            name='payment_method',
            field=models.CharField(
                choices=[('cash', 'Cash'), ('bank_transfer', 'Bank Transfer'), ('card', 'Card'),
                         ('mpesa', 'M-Pesa'), ('pos', 'POS'), ('other', 'Other')],
                default='cash',
                max_length=20
            ),
        ),

        # Add receipt_number field WITHOUT unique initially
        migrations.AddField(
            model_name='receipt',
            name='receipt_number',
            field=models.CharField(blank=True, editable=False, max_length=30),
        ),

        # Add received_by field to Receipt
        migrations.AddField(
            model_name='receipt',
            name='received_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='receipts_received',
                to=settings.AUTH_USER_MODEL
            ),
        ),

        # Add reference_code field to Receipt
        migrations.AddField(
            model_name='receipt',
            name='reference_code',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
