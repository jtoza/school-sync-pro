import logging
from django.conf import settings
import africastalking

logger = logging.getLogger(__name__)


class AfricasTalkingSMS:
    """
    Wrapper for Africa's Talking SMS API.
    Handles sending SMS messages for result notifications.
    """
    
    def __init__(self):
        self.username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
        self.api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
        self.sender_id = getattr(settings, 'AFRICASTALKING_SENDER_ID', 'GREEN_BELLS')
        
        # Initialize Africa's Talking
        africastalking.initialize(self.username, self.api_key)
        self.sms = africastalking.SMS
    
    def send_sms(self, phone_number, message):
        """
        Send SMS to a single phone number.
        
        Args:
            phone_number (str): Phone number in format +254XXXXXXXXX or 07XXXXXXXX
            message (str): SMS message content
            
        Returns:
            dict: {'success': bool, 'message': str, 'data': dict}
        """
        try:
            # Format phone number to international format
            formatted_phone = self.format_phone_number(phone_number)
            
            if not formatted_phone:
                return {
                    'success': False,
                    'message': f'Invalid phone number: {phone_number}',
                    'data': None
                }
            
            # Send SMS
            response = self.sms.send(
                message=message,
                recipients=[formatted_phone],
                sender_id=self.sender_id
            )
            
            logger.info(f"SMS sent to {formatted_phone}: {response}")
            
            return {
                'success': True,
                'message': 'SMS sent successfully',
                'data': response
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
    
    def send_bulk_sms(self, recipients):
        """
        Send SMS to multiple recipients.
        
        Args:
            recipients (list): List of dicts with 'phone' and 'message' keys
                Example: [{'phone': '+254712345678', 'message': 'Hello'}]
                
        Returns:
            dict: {'success': bool, 'sent': int, 'failed': int, 'results': list}
        """
        results = []
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            phone = recipient.get('phone')
            message = recipient.get('message')
            
            if not phone or not message:
                failed_count += 1
                results.append({
                    'phone': phone,
                    'success': False,
                    'error': 'Missing phone or message'
                })
                continue
            
            result = self.send_sms(phone, message)
            
            if result['success']:
                sent_count += 1
            else:
                failed_count += 1
            
            results.append({
                'phone': phone,
                'success': result['success'],
                'error': result['message'] if not result['success'] else None
            })
        
        return {
            'success': sent_count > 0,
            'sent': sent_count,
            'failed': failed_count,
            'results': results
        }
    
    @staticmethod
    def format_phone_number(phone):
        """
        Format phone number to international format (+254XXXXXXXXX).
        
        Args:
            phone (str): Phone number in various formats
            
        Returns:
            str: Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove spaces, dashes, and other characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle Kenyan numbers
        if phone.startswith('254'):
            # Already in international format
            return f'+{phone}'
        elif phone.startswith('0'):
            # Local format (0712345678) -> +254712345678
            return f'+254{phone[1:]}'
        elif phone.startswith('7') and len(phone) == 9:
            # Missing leading 0 (712345678) -> +254712345678
            return f'+254{phone}'
        
        # If it doesn't match Kenyan format, try to add +254
        if len(phone) == 9:
            return f'+254{phone}'
        
        return None


def format_result_message(student, results, session, term):
    """
    Format student results into SMS message.
    
    Args:
        student: Student object
        results: QuerySet of Result objects
        session: AcademicSession object
        term: AcademicTerm object
        
    Returns:
        str: Formatted SMS message
    """
    if not results.exists():
        return None
    
    # Header
    message = f"Green Bells Academy\n"
    message += f"RESULTS - {term.name}, {session.name}\n\n"
    message += f"{student.get_short_name()} ({student.registration_number})\n"
    
    # Calculate totals
    total_score = 0
    max_score = 0
    subject_count = results.count()
    
    # Add subject results (compact format for SMS)
    subject_lines = []
    for result in results[:5]:  # Limit to 5 subjects to keep SMS short
        subject_name = result.subject.name[:8]  # Shorten subject name
        score = result.total_score()
        grade = result.grade()
        total_score += score
        max_score += 100
        subject_lines.append(f"{subject_name}:{score}({grade})")
    
    message += " ".join(subject_lines)
    
    if subject_count > 5:
        message += f" +{subject_count - 5} more"
    
    message += "\n\n"
    
    # Overall performance
    if max_score > 0:
        percentage = round((total_score / max_score) * 100, 1)
        overall_grade = get_overall_grade(percentage)
        message += f"Overall: {percentage}% ({overall_grade})\n"
    
    # Add comment if available
    first_result = results.first()
    if first_result.teacher_comment:
        comment = first_result.teacher_comment[:50]  # Limit comment length
        message += f"\n{comment}"
    
    return message


def get_overall_grade(percentage):
    """
    Convert percentage to grade.
    
    Args:
        percentage (float): Overall percentage
        
    Returns:
        str: Grade letter
    """
    if percentage >= 80:
        return 'A'
    elif percentage >= 75:
        return 'A-'
    elif percentage >= 70:
        return 'B+'
    elif percentage >= 65:
        return 'B'
    elif percentage >= 60:
        return 'B-'
    elif percentage >= 55:
        return 'C+'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 45:
        return 'C-'
    elif percentage >= 40:
        return 'D+'
    elif percentage >= 35:
        return 'D'
    elif percentage >= 30:
        return 'D-'
    else:
        return 'E'


def send_result_sms(student, session, term):
    """
    Send result SMS for a single student.
    
    Args:
        student: Student object
        session: AcademicSession object
        term: AcademicTerm object
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    from .models import Result
    
    # Get student results
    results = Result.objects.filter(
        student=student,
        session=session,
        term=term
    ).select_related('subject')
    
    if not results.exists():
        return {
            'success': False,
            'message': f'No results found for {student.get_short_name()}'
        }
    
    # Get parent phone number
    phone = student.parent_mobile_number or student.guardian_phone
    
    if not phone:
        return {
            'success': False,
            'message': f'No phone number for {student.get_short_name()}'
        }
    
    # Format message
    message = format_result_message(student, results, session, term)
    
    if not message:
        return {
            'success': False,
            'message': 'Failed to format message'
        }
    
    # Send SMS
    sms_client = AfricasTalkingSMS()
    result = sms_client.send_sms(phone, message)
    
    return result


def send_bulk_result_sms(students, session, term):
    """
    Send result SMS to multiple students.
    
    Args:
        students: QuerySet of Student objects
        session: AcademicSession object
        term: AcademicTerm object
        
    Returns:
        dict: {'success': bool, 'sent': int, 'failed': int, 'details': list}
    """
    from .models import Result
    
    recipients = []
    details = []
    
    for student in students:
        # Get results
        results = Result.objects.filter(
            student=student,
            session=session,
            term=term
        ).select_related('subject')
        
        if not results.exists():
            details.append({
                'student': student.get_short_name(),
                'success': False,
                'error': 'No results found'
            })
            continue
        
        # Get phone number
        phone = student.parent_mobile_number or student.guardian_phone
        
        if not phone:
            details.append({
                'student': student.get_short_name(),
                'success': False,
                'error': 'No phone number'
            })
            continue
        
        # Format message
        message = format_result_message(student, results, session, term)
        
        if not message:
            details.append({
                'student': student.get_short_name(),
                'success': False,
                'error': 'Failed to format message'
            })
            continue
        
        recipients.append({
            'phone': phone,
            'message': message,
            'student': student.get_short_name()
        })
    
    # Send bulk SMS
    if not recipients:
        return {
            'success': False,
            'sent': 0,
            'failed': len(students),
            'details': details
        }
    
    sms_client = AfricasTalkingSMS()
    
    sent_count = 0
    failed_count = 0
    
    for recipient in recipients:
        result = sms_client.send_sms(recipient['phone'], recipient['message'])
        
        if result['success']:
            sent_count += 1
            details.append({
                'student': recipient['student'],
                'success': True,
                'error': None
            })
        else:
            failed_count += 1
            details.append({
                'student': recipient['student'],
                'success': False,
                'error': result['message']
            })
    
    return {
        'success': sent_count > 0,
        'sent': sent_count,
        'failed': failed_count,
        'details': details
    }
