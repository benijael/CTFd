
import requests
from CTFd.utils import get_config

class ResendEmailProvider:
    @staticmethod
    def sendmail(addr, text, subject):
        api_key = get_config("mail_password")
        from_addr = get_config("mailfrom_addr") or "noreply@soopha-network.com"
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": from_addr,
                "to": [addr],
                "subject": subject,
                "text": text
            }
        )
        
        if response.status_code == 200:
            return True, "Email sent"
        return False, response.text
