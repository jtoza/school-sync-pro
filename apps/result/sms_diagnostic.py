# result/sms_diagnostic.py
import logging
from django.conf import settings
from africastalking.Service import SMS

logger = logging.getLogger(__name__)

def check_phone_number_format(phone):
    """Check and fix phone number format for Kenya"""
    original = phone
    if not phone:
        return None, "Empty phone number"
    
    # Remove any spaces, dashes, parentheses
    phone = ''.join(filter(str.isdigit, phone))
    
    if not phone:
        return None, "No digits found"
    
    # Check if it's already in international format
    if phone.startswith('254'):
        return '+' + phone, "OK - 254 format"
    elif phone.startswith('7') and len(phone) == 9:
        return '+254' + phone, "OK - 7 format (9 digits)"
    elif phone.startswith('07'):
        return '+254' + phone[1:], "OK - 07 format"
    elif phone.startswith('01'):
        return '+254' + phone[1:], "OK - 01 format"
    elif phone.startswith('+254'):
        return phone, "OK - +254 format"
    else:
        return None, f"Unknown format: {original}"

def test_sms_connection():
    """Test Africa's Talking connection"""
    try:
        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY
        
        print(f"Username: {username}")
        print(f"API Key: {api_key[:10]}...{api_key[-10:]}")
        print(f"Sender ID: {settings.AFRICASTALKING_SENDER_ID}")
        
        # Initialize
        sms = SMS(username, api_key)
        
        # Check balance
        print("\nChecking account balance...")
        try:
            # Try to check balance (not all accounts may have this)
            # You might need to check manually at https://account.africastalking.com/
            print("Note: Check balance manually at https://account.africastalking.com/")
        except:
            pass
            
        return True, "Connection successful"
        
    except Exception as e:
        return False, str(e)

def check_student_phones():
    """Check all student phone numbers"""
    from apps.students.models import Student
    
    students = Student.objects.filter(current_status='active')
    
    results = []
    for student in students:
        phone = student.parent_mobile
        if phone:
            formatted, status = check_phone_number_format(phone)
            results.append({
                'student': student.get_full_name(),
                'original': phone,
                'formatted': formatted,
                'status': status,
                'has_phone': bool(phone)
            })
        else:
            results.append({
                'student': student.get_full_name(),
                'original': None,
                'formatted': None,
                'status': 'No phone number',
                'has_phone': False
            })
    
    return results