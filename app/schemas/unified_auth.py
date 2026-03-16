import re
from typing import Optional
from pydantic import BaseModel, EmailStr, model_validator, field_validator
import phonenumbers

class UnifiedRegisterRequest(BaseModel):
    email: Optional[EmailStr] = None
    country_code: str
    number: str
    password: str
    full_name: Optional[str] = None
    second_name: Optional[str] = None
    phone_number: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @model_validator(mode='after')
    def validate_contact_methods(self) -> 'UnifiedRegisterRequest':
        try:
            # Normalize country code
            cc = self.country_code
            if cc and cc.isdigit():
                 cc = f"+{cc}"
            if cc and not cc.startswith("+"):
                 cc = f"+{cc}"
            self.country_code = cc
            
            full_number = f"{self.country_code}{self.number}"
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
            
            self.phone_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
             raise ValueError("Invalid phone number format")
             
        return self


class UnifiedLoginRequest(BaseModel):
    email: Optional[str] = None
    country_code: str
    number: str
    password: str
    phone_number: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_login_methods(self) -> 'UnifiedLoginRequest':
        try:
            cc = self.country_code
            if cc and cc.isdigit():
                 cc = f"+{cc}"
            if cc and not cc.startswith("+"):
                 cc = f"+{cc}"
            self.country_code = cc
            
            full_number = f"{self.country_code}{self.number}"
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
            
            self.phone_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
        except phonenumbers.NumberParseException:
             raise ValueError("Invalid phone number format")
             
        return self
