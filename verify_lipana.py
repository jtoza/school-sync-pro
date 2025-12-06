import os
import django
from unittest.mock import patch, MagicMock

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')
django.setup()

from apps.finance.lipana import LipanaMpesa

@patch('requests.get')
@patch('requests.post')
def test_lipana(mock_post, mock_get):
    print("Testing LipanaMpesa integration...")
    
    # Mock Access Token Response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'access_token': 'test_token'}
    
    # Mock STK Push Response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'ResponseCode': '0',
        'ResponseDescription': 'Success',
        'CustomerMessage': 'Success'
    }
    
    lipana = LipanaMpesa()
    
    # Test Get Access Token
    token = lipana.get_access_token()
    print(f"Access Token: {token}")
    assert token == 'test_token'
    
    # Test STK Push
    response = lipana.initiate_stk_push(
        phone_number="254712345678",
        amount=100,
        account_reference="INV-001",
        transaction_desc="Test Payment",
        callback_url="http://localhost:8000/callback"
    )
    
    print(f"STK Push Response: {response}")
    assert response['success'] == True
    
    print("Verification Successful!")

if __name__ == "__main__":
    test_lipana()
