import random
import string
from datetime import datetime, timedelta
from typing import Optional
from app.zenstack_client import zenstack_client
from app.config import settings
import httpx

class OTPService:
    def __init__(self):
        import os
        self.otp_length = 6
        self.otp_expiry_minutes = 1  # OTP expires in 1 minute (60 seconds)
        # SMS service configuration
        self.sms_service = os.getenv("SMS_SERVICE", "console")  
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    async def send_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS using configured service"""
        try:
            if self.sms_service == "twilio":
                return await self._send_twilio_sms(phone_number, message)
            elif self.sms_service == "textlocal":
                return await self._send_textlocal_sms(phone_number, message)
            else:
                # Fallback to console for development
                print(f"SMS to {phone_number}: {message}")
                return {"success": True, "message": "SMS sent (console)"}
        except Exception as e:
            print(f"SMS sending failed: {str(e)}")
            return {"success": False, "message": f"SMS sending failed: {str(e)}"}
    
    async def _send_twilio_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS via Twilio"""
        try:
            # Format phone number (add +91 for India)
            if not phone_number.startswith('+'):
                phone_number = f"+91{phone_number}"
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            data = {
                "From": self.twilio_phone_number,
                "To": phone_number,
                "Body": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.twilio_account_sid, self.twilio_auth_token)
                )
                
                if response.status_code == 201:
                    return {"success": True, "message": "SMS sent successfully"}
                else:
                    return {"success": False, "message": f"Twilio error: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "message": f"Twilio SMS failed: {str(e)}"}
    
    async def _send_textlocal_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS via TextLocal (India)"""
        try:
            # TextLocal API configuration
            textlocal_api_key = "YOUR_TEXTLOCAL_API_KEY"
            textlocal_sender = "BOLISETTI"
            
            url = "https://api.textlocal.in/send/"
            data = {
                "apikey": textlocal_api_key,
                "numbers": phone_number,
                "message": message,
                "sender": textlocal_sender
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                result = response.json()
                
                if result.get("status") == "success":
                    return {"success": True, "message": "SMS sent successfully"}
                else:
                    return {"success": False, "message": f"TextLocal error: {result.get('errors', 'Unknown error')}"}
                    
        except Exception as e:
            return {"success": False, "message": f"TextLocal SMS failed: {str(e)}"}
    
    async def send_otp(self, phone_number: str) -> dict:
        """
        Generate and send OTP to phone number
        In production, this would integrate with SMS service like Twilio
        """
        try:
            # Generate OTP
            otp = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Store OTP in database
            otp_data = {
                "phoneNumber": phone_number,
                "otp": otp,
                "expiresAt": expires_at.isoformat() + "Z",
                "isUsed": False
            }
            
            result = await zenstack_client.create_otp(otp_data)
            
            # Send SMS with OTP
            sms_message = f"Your OTP for Bollisetti App is: {otp}. Valid for {self.otp_expiry_minutes} minutes. Do not share this code with anyone."
            sms_result = await self.send_sms(phone_number, sms_message)
            
            if sms_result["success"]:
                return {
                    "success": True,
                    "message": "OTP sent successfully to your phone",
                    "expires_in": self.otp_expiry_minutes * 60
                }
            else:
                # If SMS fails, still return success but log the error
                print(f"SMS sending failed: {sms_result['message']}")
                return {
                    "success": True,
                    "message": "OTP generated successfully (SMS may not be delivered)",
                    "otp": otp,  # Fallback for development
                    "expires_in": self.otp_expiry_minutes * 60
                }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send OTP: {str(e)}"
            }
    
    async def verify_otp(self, phone_number: str, otp: str) -> dict:
        """
        Verify OTP for phone number
        """
        try:
            # Get OTP from database
            otp_record = await zenstack_client.get_otp_by_phone(phone_number)
            
            if not otp_record or 'data' not in otp_record:
                return {
                    "success": False,
                    "message": "OTP not found"
                }
            
            otp_data = otp_record['data']
            
            # Check if OTP is already used
            if otp_data.get('isUsed', False):
                return {
                    "success": False,
                    "message": "OTP already used"
                }
            
            # Check if OTP is expired
            expires_at_str = otp_data['expiresAt']
            # Parse the stored datetime string (remove Z and parse as UTC)
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', ''))
            current_time = datetime.utcnow()
            
            if current_time > expires_at:
                return {
                    "success": False,
                    "message": "OTP expired"
                }
            
            # Check if OTP matches
            stored_otp = otp_data.get('otp')
            if stored_otp != otp:
                return {
                    "success": False,
                    "message": "Invalid OTP"
                }
            
            # Mark OTP as used
            await zenstack_client.mark_otp_used(otp_data['id'])
            
            return {
                "success": True,
                "message": "OTP verified successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to verify OTP: {str(e)}"
            }
    
    async def cleanup_expired_otps(self):
        """Clean up expired OTPs from database"""
        try:
            await zenstack_client.cleanup_expired_otps()
        except Exception as e:
            print(f"Error cleaning up expired OTPs: {str(e)}")

# Global OTP service instance
otp_service = OTPService()
