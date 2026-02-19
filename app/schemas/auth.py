from pydantic import BaseModel, model_validator
import phonenumbers

class LoginRequest(BaseModel):
    country_code: str
    number: str
    password: str
    phone_number: str | None = None

    @model_validator(mode='after')
    def validate_phone(self) -> 'LoginRequest':
        try:
            # Normalize country code: Ensure it starts with + if it looks like a country code (digits)
            if self.country_code and self.country_code.isdigit():
                 self.country_code = f"+{self.country_code}"
            
            # Or just check if missing +
            if self.country_code and not self.country_code.startswith("+"):
                 self.country_code = f"+{self.country_code}"
                 
            full_number = f"{self.country_code}{self.number}"
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
            
            self.phone_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
            return self
        except phonenumbers.NumberParseException:
             raise ValueError("Invalid phone number format")

class Token(BaseModel):
    access_token: str
    token_type: str