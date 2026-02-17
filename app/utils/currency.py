import phonenumbers

def get_currency_from_phone_code(phone_number: str) -> str:
    """
    Get currency code based on phone number country prefix.
    
    Supported Mappings:
    - +971 (UAE) -> AED
    - +91 (India) -> INR
    - +966 (Saudi Arabia) -> SAR
    - +968 (Oman) -> OMR
    - Others -> USD
    """
    if not phone_number:
        return "USD"
        
    try:
        # Parse the phone number to get country code
        # We assume the input is either a full E164 number or checks against prefixes manually
        # Since phonenumbers might need a region to parse strict validity, 
        # we can check prefixes directly for simplicity and speed if we know the format.
        
        # Simple prefix check
        if phone_number.startswith("+971"):
            return "AED"
        elif phone_number.startswith("+91"):
            return "INR"
        elif phone_number.startswith("+966"):
            return "SAR"
        elif phone_number.startswith("+968"):
            return "OMR"
        
        # Fallback to USD for all other regions (including US +1)
        return "USD"
        
    except Exception:
        return "USD"

def get_currency_symbol(currency_code: str) -> str:
    """Get symbol for currency code"""
    symbols = {
        "USD": "$",
        "AED": "AED",
        "INR": "₹",
        "SAR": "SAR",
        "OMR": "OMR"
    }
    return symbols.get(currency_code, "$")
