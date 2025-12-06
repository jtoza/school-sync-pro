import os
import django
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

from apps.finance.lipana import LipanaMpesa

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_stk():
    print("Initiating Real STK Push...")
    
    lipana = LipanaMpesa()
    
    # Test Data
    phone_number = "254796824181" # User provided number
    amount = 10 # Small amount for testing
    account_reference = "TEST-PAY"
    transaction_desc = "Test Payment"
    callback_url = "https://school-management-framework.onrender.com/finance/mpesa/callback/" # Using one of the allowed hosts or a dummy if local
    # Note: If running locally, callback won't reach localhost. But STK push should still arrive on phone.
    
    print(f"Phone: {phone_number}, Amount: {amount}")
    
    response = lipana.initiate_stk_push(
        phone_number=phone_number,
        amount=amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc,
        callback_url=callback_url
    )
    
    print(f"Response: {response}")

if __name__ == "__main__":
    test_real_stk()
