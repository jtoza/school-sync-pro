# Parent Portal - Testing Guide (Updated)

## New Design: Student ID Lookup System

The parent portal has been redesigned for easier access. **No parent accounts needed!** Parents simply enter their child's student ID to view fee information.

## How to Access

### 1. Visit the Parent Portal
Navigate to: **http://localhost:8000/parents/**

You'll see a landing page with:
- Welcome message
- Student ID lookup form
- Feature highlights

### 2. Enter Student ID
In the search form, enter either:
- **Student Registration Number** (e.g., `SCI/20/0001`)
- **Student ID** (numeric, e.g., `1`, `2`, `3`)

### 3. View Fee Details
After submitting, you'll be redirected to the fee details page showing:
- Student information
- Financial summary (Total Payable, Amount Paid, Outstanding Balance)
- Invoice history
- Payment history with receipts

## Test Data

Use these student IDs to test (from your existing database):
- Look for students in your database
- Use their registration numbers or numeric IDs

To find available student IDs, run:
```bash
python manage.py shell
```

Then:
```python
from apps.students.models import Student
students = Student.objects.all()
for s in students:
    print(f"ID: {s.id} | Reg: {s.registration_number} | Name: {s.get_full_name()}")
```

## Features

✓ **No Login Required** - Public access via student ID
✓ **Simple Lookup** - Just enter student ID or registration number
✓ **Financial Summary** - Clear overview of fees and payments
✓ **Invoice History** - All invoices by session and term
✓ **Payment History** - Track all payments with download options
✓ **Modern UI** - Beautiful gradient design with responsive layout

## URLs

- **Landing Page:** http://localhost:8000/parents/
- **Fee Details:** http://localhost:8000/parents/student/[ID]/fees/

## Security Note

This is a public-facing portal. In production, you may want to add:
- CAPTCHA to prevent automated lookups
- Rate limiting
- Optional PIN/password verification
- Audit logging of lookups

## Next Steps

1. Test the lookup with different student IDs
2. Verify fee calculations are correct
3. Check that all invoices and payments display properly
4. Test on mobile devices for responsiveness
