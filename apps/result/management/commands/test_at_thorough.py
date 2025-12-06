# result/management/commands/test_at_thorough.py
from django.core.management.base import BaseCommand
from django.conf import settings
import africastalking

class Command(BaseCommand):
    help = 'Thorough Africa\'s Talking test with known valid numbers'
    
    def handle(self, *args, **kwargs):
        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY
        
        print("=" * 70)
        print("COMPREHENSIVE AFRICA'S TALKING DIAGNOSTIC")
        print("=" * 70)
        
        # Initialize
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        # Test with different sender IDs
        sender_ids = ['AFRICASTALKING', 'INFO', 'ALERT']
        
        # Test numbers (using common Kenyan prefixes)
        # Note: 25470 might be invalid. Let's test with other prefixes
        test_cases = [
            {
                'name': 'Safaricom 25471',
                'number': '254712345678',  # This is a TEST pattern
                'valid': True
            },
            {
                'name': 'Safaricom 25476',
                'number': '254761234567',
                'valid': True
            },
            {
                'name': 'Airtel 25473',
                'number': '254731234567',
                'valid': True
            },
            {
                'name': 'Telkom 25477',
                'number': '254771234567',
                'valid': True
            },
            {
                'name': 'Your number formatted',
                'number': '254704892525',
                'valid': False  # Might be the issue!
            },
            {
                'name': 'Without country code',
                'number': '704892525',
                'valid': False
            }
        ]
        
        message = "Test SMS from Green Bells - Diagnostic"
        
        for sender_id in sender_ids:
            print(f"\n📤 Testing Sender ID: {sender_id}")
            print("-" * 40)
            
            for test in test_cases:
                print(f"\n  Testing: {test['name']}")
                print(f"  Number: {test['number']}")
                
                try:
                    # Try sending
                    response = sms.send(message, [test['number']], sender_id)
                    status = response['SMSMessageData']['Recipients'][0]['status']
                    
                    print(f"  Result: ✅ {status}")
                    
                    if status == 'Success':
                        print(f"  Message ID: {response['SMSMessageData']['Recipients'][0]['messageId']}")
                        
                except Exception as e:
                    print(f"  Result: ❌ {str(e)}")
                    
                    # Specific error analysis
                    error = str(e)
                    if 'invalid phone' in error.lower():
                        if test['number'].startswith('25470'):
                            print(f"  Note: 25470 might not be a valid Kenyan mobile prefix")
                            print(f"  Valid prefixes: 25471, 25472, 25473, 25474, 25475, 25476, 25477, 25478, 25479")
        
        print("\n" + "=" * 70)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 70)
        print("\n🔍 Key Finding: Your number 0704892525 → 254704892525")
        print("   The '25470' prefix might be invalid!")
        print("\n🛠️  Possible Solutions:")
        print("   1. Double-check the actual phone number")
        print("   2. Try a different valid Kenyan number")
        print("   3. Contact Africa's Talking support")
        print("\n📱 Quick Test: Try with 254712345678 (test pattern)")