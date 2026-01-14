# final_sms_test.py
import africastalking
import json

def comprehensive_test():
    print("🎯 FINAL SMS TEST WITH CORRECT CREDENTIALS")
    print("=" * 60)
    
    # CORRECT credentials from dashboard
    username = "greenbells"
    api_key = "atsk_d7bd89991cb10b9e2c80a886e499c8a33e61d600384b9290280c3bd95fe6b24b28fd74f8"
    
    print(f"✓ Username: {username}")
    print(f"✓ API Key: {api_key[:15]}...{api_key[-15:]}")
    
    # Initialize
    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    
    # Test different scenarios
    test_cases = [
        {
            "name": "Test with your Safaricom number",
            "number": "254704892525",
            "sender": "AFRICASTALKING",  # Default, should work
            "message": "Test 1: Default sender from Green Bells"
        },
        {
            "name": "Test with short message",
            "number": "254704892525",
            "sender": "INFO",  # Another default
            "message": "Test 2: Short test"
        },
        {
            "name": "Test with GREEN_BELLS sender",
            "number": "254704892525",
            "sender": "GREEN_BELLS",
            "message": "Test 3: Using GREEN_BELLS sender ID"
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*50}")
        
        print(f"📱 To: {test['number']}")
        print(f"📤 From: {test['sender']}")
        print(f"📝 Message: '{test['message']}'")
        
        try:
            response = sms.send(test['message'], [test['number']], test['sender'])
            
            print(f"\n✅ SUCCESS!")
            
            # Pretty print response
            recipient = response['SMSMessageData']['Recipients'][0]
            print(f"📊 Details:")
            print(f"  Status: {recipient['status']}")
            print(f"  Message ID: {recipient['messageId']}")
            print(f"  Cost: {recipient.get('cost', 'N/A')}")
            
            # Check if actually delivered
            if recipient['status'] == 'Success':
                print(f"🎉 SMS ACCEPTED FOR DELIVERY!")
                print(f"💡 Note: Delivery takes 1-30 seconds")
                
                # Save successful configuration
                if test['sender'] == 'GREEN_BELLS':
                    print(f"\n🌟 Perfect! GREEN_BELLS sender ID is working!")
                else:
                    print(f"\n⚠️  Using {test['sender']} instead of GREEN_BELLS")
                    
            elif recipient['status'] == 'Sent':
                print(f"📤 SMS SENT!")
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            
            # Analyze specific errors
            error_msg = str(e).lower()
            
            if 'invalid senderid' in error_msg or 'sender id' in error_msg:
                print(f"\n📛 Sender ID issue detected!")
                print(f"   '{test['sender']}' might not be approved yet.")
                print(f"   Solution: Use 'AFRICASTALKING' for now")
                
            elif 'insufficient' in error_msg:
                print(f"\n💰 Balance issue!")
                print(f"   Check: https://account.africastalking.com/apps/sms/balance")
                
            elif 'invalid phone' in error_msg:
                print(f"\n📞 Phone number issue!")
                print(f"   Number: {test['number']}")
                print(f"   Try: 254714892525 (if 25470 is problematic)")
                
    print(f"\n{'='*60}")
    print("🎯 RECOMMENDATIONS:")
    print("=" * 60)
    
    print("1. If 'AFRICASTALKING' sender works, use it temporarily")
    print("2. Contact support to approve 'GREEN_BELLS' sender ID")
    print("3. Check SMS delivery reports in dashboard")
    print("4. Monitor balance after sending")

if __name__ == "__main__":
    comprehensive_test()