# result/management/commands/test_sms.py
from django.core.management.base import BaseCommand
from django.conf import settings
import africastalking
import re

class Command(BaseCommand):
    help = 'Test Africa\'s Talking SMS configuration'
    
    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Phone number to test with')
    
    def format_phone(self, phone):
        """Properly format phone number for Africa's Talking"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        if not digits:
            return None
        
        # Kenya specific formatting
        if digits.startswith('254') and len(digits) == 12:
            return digits  # Africa's Talking expects without +
        elif digits.startswith('7') and len(digits) == 9:
            return '254' + digits
        elif digits.startswith('07') and len(digits) == 10:
            return '254' + digits[1:]
        elif digits.startswith('01') and len(digits) == 10:
            return '254' + digits[1:]
        else:
            # Try to guess
            if len(digits) == 9 and digits[0] in ['1', '7']:
                return '254' + digits
            elif len(digits) == 10 and digits.startswith('0'):
                return '254' + digits[1:]
            else:
                return None
    
    def handle(self, *args, **kwargs):
        # Initialize SDK
        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY
        
        self.stdout.write("=" * 60)
        self.stdout.write("Africa's Talking SMS Diagnostic Test")
        self.stdout.write("=" * 60)
        
        self.stdout.write(f"\n📱 Configuration:")
        self.stdout.write(f"   Username: {username}")
        self.stdout.write(f"   Sender ID: {settings.AFRICASTALKING_SENDER_ID}")
        self.stdout.write(f"   API Key: {api_key[:8]}...{api_key[-8:]}")
        
        # Get test phone number
        test_phone = kwargs['phone'] or input("\n📞 Enter phone number to test (e.g., 0712345678): ")
        
        # Format the phone number
        formatted = self.format_phone(test_phone)
        
        self.stdout.write(f"\n🔍 Phone Number Analysis:")
        self.stdout.write(f"   Original: {test_phone}")
        self.stdout.write(f"   Formatted: {formatted}")
        
        if not formatted:
            self.stdout.write(self.style.ERROR("❌ Invalid phone number format!"))
            self.stdout.write("\n📝 Valid Kenya formats:")
            self.stdout.write("   - 0712345678")
            self.stdout.write("   - 712345678")
            self.stdout.write("   - 254712345678")
            return
        
        message = "Test SMS from Green Bells Academy. If you receive this, SMS system is working!"
        
        self.stdout.write(f"\n📨 Test Details:")
        self.stdout.write(f"   To: {formatted}")
        self.stdout.write(f"   From: {settings.AFRICASTALKING_SENDER_ID}")
        self.stdout.write(f"   Message: '{message[:50]}...'")
        
        # Initialize Africa's Talking
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        self.stdout.write("\n⏳ Sending test SMS...")
        
        try:
            response = sms.send(message, [formatted], settings.AFRICASTALKING_SENDER_ID)
            
            self.stdout.write(self.style.SUCCESS("\n✅ SMS Sent Successfully!"))
            self.stdout.write(f"\n📊 Response Details:")
            
            # Pretty print the response
            for recipient in response['SMSMessageData']['Recipients']:
                self.stdout.write(f"   Number: {recipient['number']}")
                self.stdout.write(f"   Status: {recipient['status']}")
                self.stdout.write(f"   Message ID: {recipient['messageId']}")
                if 'cost' in recipient:
                    self.stdout.write(f"   Cost: {recipient['cost']}")
                if 'statusCode' in recipient:
                    self.stdout.write(f"   Status Code: {recipient['statusCode']}")
            
            # Show the full response for debugging
            self.stdout.write(f"\n🔧 Raw Response:")
            self.stdout.write(str(response))
            
            # Check if it's a sandbox response
            if response.get('SMSMessageData', {}).get('Message') == 'Sent to 1/1 Total Cost: KES 0':
                self.stdout.write(self.style.WARNING("\n⚠️  NOTE: This appears to be a SANDBOX response!"))
                self.stdout.write("    Sandbox mode sends free SMS but only to test numbers.")
                self.stdout.write("    Switch to production credentials for real SMS.")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error sending SMS: {str(e)}"))
            
            # Common error patterns
            error_str = str(e).lower()
            if 'invalid phone' in error_str:
                self.stdout.write(self.style.WARNING("\n🔍 Phone number issue detected!"))
                self.stdout.write("   Africa's Talking expects numbers in format: 2547XXXXXXXX")
                self.stdout.write("   Without the + sign!")
                
            elif 'insufficient balance' in error_str or 'balance' in error_str:
                self.stdout.write(self.style.WARNING("\n💰 Insufficient balance!"))
                self.stdout.write("   Check your Africa's Talking account balance at:")
                self.stdout.write("   https://account.africastalking.com/apps/sms/balance")
                
            elif 'senderid' in error_str or 'sender id' in error_str:
                self.stdout.write(self.style.WARNING("\n📛 Sender ID issue!"))
                self.stdout.write("   'GREEN_BELLS' might not be approved yet.")
                self.stdout.write("   Sender IDs take 24-48 hours to approve.")
                self.stdout.write("   Try using a shortcode or contact support.")
                
            elif 'authentication' in error_str or 'invalid credentials' in error_str:
                self.stdout.write(self.style.WARNING("\n🔐 Authentication issue!"))
                self.stdout.write("   Check your username and API key.")
                self.stdout.write("   Make sure you're using LIVE credentials, not sandbox.")