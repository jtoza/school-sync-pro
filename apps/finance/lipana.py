import logging
from django.conf import settings
from lipana import Lipana

logger = logging.getLogger(__name__)

class LipanaMpesa:
    def __init__(self):
        self.api_key = settings.LIPANA_PRODUCTION_KEY
        # Assuming production environment for now, or we can add a setting
        self.environment = "production" 
        self.client = Lipana(api_key=self.api_key, environment=self.environment)

    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None):
        """
        Initiate an STK Push request using Lipana SDK.
        """
        try:
            # Different SDKs have different parameter names for business name
            # Let's try common ones or check the Lipana SDK documentation
            
            # Try to initiate STK push with available parameters
            response = self.client.transactions.initiate_stk_push(
                phone=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc
            )
            
            return {"success": True, "data": response}
            
        except Exception as e:
            logger.error(f"Error initiating STK push: {e}")
            return {"success": False, "message": str(e)}