# result/management/commands/debug_at_account.py
from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json

class Command(BaseCommand):
    help = 'Debug Africa\'s Talking account issues'
    
    def handle(self, *args, **kwargs):
        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY
        
        print("=" * 70)
        print("AFRICA'S TALKING ACCOUNT DEBUG")
        print("=" * 70)
        
        print(f"\n🔐 Your Credentials:")
        print(f"   Username: {username}")
        print(f"   API Key: {api_key}")
        
        # Check 1: Test API directly
        print("\n🔍 Testing API Connection...")
        
        url = "https://api.africastalking.com/version1/user"
        headers = {
            'apiKey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        params = {'username': username}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API Connection Successful!")
                
                user_data = data.get('UserData', {})
                print(f"\n📊 Account Details:")
                print(f"   Email: {user_data.get('email', 'N/A')}")
                print(f"   Balance: {user_data.get('accountBalance', 'N/A')}")
                
                # Check apps
                apps = data.get('Apps', [])
                if apps:
                    print(f"\n📱 Your Applications:")
                    for app in apps:
                        print(f"   Name: {app.get('name')}")
                        print(f"   Status: {app.get('status')}")
                        
                        # Check SMS service
                        services = app.get('services', {})
                        if 'sms' in services:
                            sms_status = services['sms'].get('status')
                            print(f"   SMS Service: {sms_status}")
                            
                            if sms_status != 'Active':
                                print(f"   ⚠️  SMS service is NOT ACTIVE!")
                        print()
                else:
                    print("\n❌ NO APPLICATIONS FOUND!")
                    print("   You must create an application at:")
                    print("   https://account.africastalking.com/apps")
                    
            elif response.status_code == 403:
                print("❌ ERROR 403: Forbidden")
                print("   Your API key or username is incorrect!")
                print(f"   Response: {response.text}")
                
            else:
                print(f"❌ ERROR {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
        
        # Manual verification steps
        print("\n" + "=" * 70)
        print("MANUAL VERIFICATION STEPS")
        print("=" * 70)
        
        print("\n1. 🔗 Login to Africa's Talking:")
        print("   https://account.africastalking.com")
        
        print("\n2. 📱 Check Application:")
        print("   a. Go to 'Applications'")
        print("   b. Find 'greenbells' app")
        print("   c. Click on it")
        print("   d. Check if SMS service is 'Active'")
        
        print("\n3. 💰 Check Balance:")
        print("   https://account.africastalking.com/apps/sms/balance")
        
        print("\n4. 🔑 Verify API Key:")
        print("   a. Go to your app 'greenbells'")
        print("   b. Click 'Settings'")
        print("   c. Check 'API Key'")
        print("   d. Make sure it matches your .env file")
        
        print("\n5. 📞 Test with Africa's Talking Sandbox (Optional):")
        print("   Temporarily use sandbox credentials:")
        print("   AFRICASTALKING_USERNAME=sandbox")
        print("   AFRICASTALKING_API_KEY=your_sandbox_key")