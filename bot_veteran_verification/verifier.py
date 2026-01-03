import requests
import json
import time
import random
from typing import Dict, Optional
import cloudscraper

class VeteranVerifier:
    def __init__(self):
        self.session = cloudscraper.create_scraper()
        self.program_id = "690415d58971e73ca187d8c9"
        self.base_url = "https://services.sheerid.com"
        self.proxies = self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        try:
            with open('proxies.txt', 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies
        except:
            return []
    
    def get_random_proxy(self):
        """Get random proxy from list"""
        if self.proxies:
            proxy = random.choice(self.proxies)
            if ':' in proxy:
                parts = proxy.split(':')
                if len(parts) == 4:
                    # host:port:user:pass
                    return {
                        'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}',
                        'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
                    }
                else:
                    # host:port
                    return {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
        return None
    
    def get_verification_id(self, access_token: str) -> Optional[str]:
        """Get verification ID from ChatGPT API"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                'https://chatgpt.com/backend-api/sheerid/verify',
                headers=headers,
                json={'programId': self.program_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('verificationId')
            else:
                print(f"Failed to get verification ID: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting verification ID: {e}")
            return None
    
    def submit_military_status(self, verification_id: str) -> bool:
        """Submit military status (VETERAN)"""
        url = f"{self.base_url}/verify/{self.program_id}/step?verificationId={verification_id}"
        
        payload = {
            "step": "militaryStatus",
            "data": {"militaryStatus": "VETERAN"}
        }
        
        try:
            proxy = self.get_random_proxy()
            response = self.session.post(
                url,
                json=payload,
                proxies=proxy,
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def submit_personal_info(self, verification_id: str, veteran_data: Dict) -> Dict:
        """Submit personal information"""
        url = f"{self.base_url}/verify/{self.program_id}/step?verificationId={verification_id}"
        
        payload = {
            "step": "personalInfo",
            "data": {
                "firstName": veteran_data['first_name'],
                "lastName": veteran_data['last_name'],
                "birthDate": veteran_data['birth_date'],
                "branch": veteran_data['branch'],
                "dischargeDate": veteran_data['discharge_date']
            }
        }
        
        try:
            proxy = self.get_random_proxy()
            response = self.session.post(
                url,
                json=payload,
                proxies=proxy,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def wait_for_email_token(self, timeout: int = 120) -> Optional[str]:
        """Wait for email token (simulate)"""
        # In real implementation, you would:
        # 1. Connect to IMAP server
        # 2. Search for SheerID verification email
        # 3. Extract token
        
        # For demo, we'll simulate waiting
        print(f"Waiting for email token (timeout: {timeout}s)")
        
        # Simulated token (in real app, extract from email)
        # You would need email credentials in config
        return "123456"  # Replace with actual email extraction
    
    def submit_email_token(self, verification_id: str, token: str) -> Dict:
        """Submit email verification token"""
        url = f"{self.base_url}/verify/{self.program_id}/step?verificationId={verification_id}"
        
        payload = {
            "step": "emailToken",
            "data": {"token": token}
        }
        
        try:
            proxy = self.get_random_proxy()
            response = self.session.post(
                url,
                json=payload,
                proxies=proxy,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
