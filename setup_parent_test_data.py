"""
Setup script to create test data for the Parent Fee Portal
Run with: python manage.py shell < setup_parent_test_data.py
Or: python setup_parent_test_data.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

from django.contrib.auth.models import User
from apps.parents.models import Parent
from apps.students.models import Student
from apps.finance.models import Invoice, InvoiceItem, Receipt
from apps.corecode.models import AcademicSession, AcademicTerm, StudentClass
from django.utils import timezone

def create_test_data():
    print("Creating test data for Parent Fee Portal...")
    
    # Create or get a parent user
    username = 'parent1'
    password = 'testpass123'
    
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': 'parent1@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"[OK] Created user: {username}")
    else:
        print(f"[OK] User already exists: {username}")
    
    # Create or get parent
    parent, created = Parent.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': '1234567890',
            'address': '123 Test Street, Test City'
        }
    )
    
    if created:
        print(f"[OK] Created parent profile for {username}")
    else:
        print(f"[OK] Parent profile already exists for {username}")
    
    # Get or create students
    students = Student.objects.all()[:2]
    
    if not students.exists():
        print("[!] No students found in database. Please create students first.")
        return
    
    # Link students to parent
    parent.students.set(students)
    print(f"[OK] Linked {students.count()} students to parent")
    
    # Get required objects for invoices
    session = AcademicSession.objects.first()
    term = AcademicTerm.objects.first()
    student_class = StudentClass.objects.first()
    
    if not all([session, term, student_class]):
        print("[!] Missing required data (session/term/class). Please set up core data first.")
        return
    
    # Create invoices and receipts for each student
    for student in parent.students.all():
        # Check if invoice already exists
        invoice, created = Invoice.objects.get_or_create(
            student=student,
            session=session,
            term=term,
            defaults={
                'class_for': student_class,
                'balance_from_previous_term': 0,
                'status': 'active'
            }
        )
        
        if created:
            print(f"[OK] Created invoice for {student.firstname} {student.surname}")
            
            # Add invoice items
            InvoiceItem.objects.create(
                invoice=invoice,
                description='Tuition Fee',
                amount=50000
            )
            InvoiceItem.objects.create(
                invoice=invoice,
                description='Books and Materials',
                amount=10000
            )
            print(f"  [OK] Added invoice items (Total: 60,000)")
            
            # Add a payment receipt
            Receipt.objects.create(
                invoice=invoice,
                amount_paid=35000,
                date_paid=timezone.now().date(),
                comment='Partial payment - Bank Transfer'
            )
            print(f"  [OK] Added receipt (Paid: 35,000, Outstanding: 25,000)")
        else:
            print(f"[OK] Invoice already exists for {student.firstname} {student.surname}")
    
    print("\n" + "="*50)
    print("Test data setup complete!")
    print("="*50)
    print(f"\nLogin credentials:")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    print(f"\nAccess the portal at:")
    print(f"  http://localhost:8000/parents/dashboard/")
    print("="*50)

if __name__ == '__main__':
    create_test_data()
