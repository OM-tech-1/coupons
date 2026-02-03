from pydantic import BaseModel, field_validator, model_validator
import phonenumbers
from uuid import UUID

class UserBase(BaseModel):
    phone_number: str
    full_name: str | None = None
    second_name: str | None = None

class UserCreate(UserBase):
    country_code: str
    number: str
    password: str
    
    # We will override phone_number from base to be optional since we construct it
    phone_number: str | None = None

    @field_validator("phone_number", mode="before", check_fields=False)
    def assemble_phone_number(cls, v, values):
        # We construct phone_number in a model validator or pre-validator
        pass

    @model_validator(mode='after')
    def validate_phone(self) -> 'UserCreate':
        try:
            full_number = f"{self.country_code}{self.number}"
            parsed_number = phonenumbers.parse(full_number, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")
            
            # Format to E.164
            self.phone_number = phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
            return self
        except phonenumbers.NumberParseException:
             raise ValueError("Invalid phone number format")

class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool

    class Config:
        from_attributes = True
