import hashlib

class ApaarVerificationService:
    @staticmethod
    def verify_apaar(apaar_id: str) -> dict:
        """
        MOCK APAAR VERIFICATION - DEMO ONLY
        In a real application, this would call the official APAAR API.
        """
        # Validate format (mock: exactly 12 digits)
        if not apaar_id.isdigit() or len(apaar_id) != 12:
            raise ValueError("Invalid APAAR ID format")
            
        # Generate hash (don't store raw ID)
        apaar_hash = hashlib.sha256(apaar_id.encode('utf-8')).hexdigest()
        
        # Generate masked ID (e.g. ********1234)
        masked_apaar_id = f"{'*' * 8}{apaar_id[-4:]}"
        
        return {
            "masked_apaar_id": masked_apaar_id,
            "apaar_hash": apaar_hash,
            "verification_status": "VERIFIED"
        }
