import re
from pydantic import BaseModel, model_validator, field_validator
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


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("New password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("New password must contain at least one special character")
        return v

    @model_validator(mode="after")
    def passwords_must_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("confirm_password must match new_password")
        return self