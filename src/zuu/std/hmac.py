import hmac
import hashlib

def create_hmac_sha256(hmac_secret, payload : str | bytes):
    """
    Create an HMAC signature for a given payload using SHA256.
    
    Args:
        hmac_secret (str or bytes): The secret key for HMAC
        payload (str or bytes): The payload to sign
    Returns:
        str: The computed HMAC signature as a hexadecimal string
    """
    

    # Ensure inputs are bytes
    if isinstance(hmac_secret, str):
        hmac_secret = hmac_secret.encode('utf-8')
    if isinstance(payload, str):
        payload = payload.encode('utf-8')
    
    # Create HMAC using SHA256
    signature = hmac.new(hmac_secret, payload, hashlib.sha256)
    
    return signature.hexdigest()
