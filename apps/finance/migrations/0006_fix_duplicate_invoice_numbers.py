# Generated manually to fix duplicate invoice numbers
from django.db import migrations
from django.utils import timezone


def fix_duplicate_invoice_numbers(apps, schema_editor):
    """
    Find and fix any duplicate invoice numbers by regenerating them.
    """
    Invoice = apps.get_model('finance', 'Invoice')
    
    # Get all invoices ordered by id
    invoices = Invoice.objects.all().order_by('id')
    
    seen_numbers = set()
    
    for invoice in invoices:
        # If invoice_number is None or duplicate, regenerate it
        if invoice.invoice_number is None or invoice.invoice_number in seen_numbers:
            # Generate a new unique invoice number
            today = timezone.now().strftime('%Y%m%d')
            prefix = f"INV-{today}-"
            seq = 1
            
            # Find next available number
            while True:
                candidate = f"{prefix}{seq:06d}"
                if candidate not in seen_numbers and not Invoice.objects.filter(invoice_number=candidate).exists():
                    invoice.invoice_number = candidate
                    invoice.save(update_fields=['invoice_number'])
                    seen_numbers.add(candidate)
                    break
                seq += 1
        else:
            seen_numbers.add(invoice.invoice_number)


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_alter_invoice_invoice_number_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_invoice_numbers, reverse_code=migrations.RunPython.noop),
    ]
