from cryptography.fernet import Fernet
from flask import current_app

class EncryptionService:
    @staticmethod
    def get_cipher():
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            # Fallback for dev if no key is provided. In prod, this should fail.
            key = Fernet.generate_key()
            current_app.config['ENCRYPTION_KEY'] = key.decode('utf-8')
        
        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode('utf-8')
            
        return Fernet(key)

    @classmethod
    def encrypt(cls, data: str) -> str:
        if not data:
            return None
        cipher = cls.get_cipher()
        return cipher.encrypt(data.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        if not encrypted_data:
            return None
        cipher = cls.get_cipher()
        return cipher.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
