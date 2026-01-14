"""
Script to fix duplicate invoice and receipt numbers in the database.
This script directly updates the database to ensure all numbers are unique.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

from apps.finance.models import Invoice, Receipt
from django.utils import timezone
from django.db import transaction

def fix_duplicate_invoice_numbers():
    """
    Find and fix any duplicate or NULL invoice numbers.
    """
    print("Checking for duplicate or NULL invoice numbers...")
    
    # Get all invoices ordered by id
    invoices = Invoice.objects.all().order_by('id')
    
    seen_numbers = set()
    fixed_count = 0
    
    with transaction.atomic():
        for invoice in invoices:
            # If invoice_number is None or duplicate, regenerate it
            if invoice.invoice_number is None or invoice.invoice_number in seen_numbers:
                print(f"Fixing invoice ID {invoice.id}: {invoice.invoice_number}")
                
                # Generate a new unique invoice number
                today = timezone.now().strftime('%Y%m%d')
                prefix = f"INV-{today}-"
                seq = 1
                
                # Find next available number
                while True:
                    candidate = f"{prefix}{seq:06d}"
                    if candidate not in seen_numbers and not Invoice.objects.filter(invoice_number=candidate).exists():
                        # Use update to bypass the save method
                        Invoice.objects.filter(id=invoice.id).update(invoice_number=candidate)
                        seen_numbers.add(candidate)
                        fixed_count += 1
                        print(f"  -> Updated to: {candidate}")
                        break
                    seq += 1
            else:
                seen_numbers.add(invoice.invoice_number)
    
    print(f"\nFixed {fixed_count} invoice(s)")
    print(f"Total invoices: {invoices.count()}")
    print(f"Unique invoice numbers: {len(seen_numbers)}")
    
    # Verify no duplicates remain
    from django.db.models import Count
    duplicates = Invoice.objects.values('invoice_number').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicates.exists():
        print("\nWARNING: Duplicates still exist:")
        for dup in duplicates:
            print(f"  {dup['invoice_number']}: {dup['count']} occurrences")
    else:
        print("\nAll invoice numbers are now unique!")

def fix_duplicate_receipt_numbers():
    """
    Find and fix any duplicate or NULL receipt numbers.
    """
    print("\n" + "="*60)
    print("Checking for duplicate or NULL receipt numbers...")
    
    # Get all receipts ordered by id
    receipts = Receipt.objects.all().order_by('id')
    
    seen_numbers = set()
    fixed_count = 0
    
    with transaction.atomic():
        for receipt in receipts:
            # If receipt_number is None or duplicate, regenerate it
            if receipt.receipt_number is None or receipt.receipt_number in seen_numbers:
                print(f"Fixing receipt ID {receipt.id}: {receipt.receipt_number}")
                
                # Generate a new unique receipt number
                today = timezone.now().strftime('%Y%m%d')
                prefix = f"RCPT-{today}-"
                seq = 1
                
                # Find next available number
                while True:
                    candidate = f"{prefix}{seq:06d}"
                    if candidate not in seen_numbers and not Receipt.objects.filter(receipt_number=candidate).exists():
                        # Use update to bypass the save method
                        Receipt.objects.filter(id=receipt.id).update(receipt_number=candidate)
                        seen_numbers.add(candidate)
                        fixed_count += 1
                        print(f"  -> Updated to: {candidate}")
                        break
                    seq += 1
            else:
                seen_numbers.add(receipt.receipt_number)
    
    print(f"\nFixed {fixed_count} receipt(s)")
    print(f"Total receipts: {receipts.count()}")
    print(f"Unique receipt numbers: {len(seen_numbers)}")
    
    # Verify no duplicates remain
    from django.db.models import Count
    duplicates = Receipt.objects.values('receipt_number').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicates.exists():
        print("\nWARNING: Duplicates still exist:")
        for dup in duplicates:
            print(f"  {dup['receipt_number']}: {dup['count']} occurrences")
    else:
        print("\nAll receipt numbers are now unique!")

if __name__ == '__main__':
    fix_duplicate_invoice_numbers()
    fix_duplicate_receipt_numbers()
    print("\n" + "="*60)
    print("DONE! All numbers have been fixed.")

