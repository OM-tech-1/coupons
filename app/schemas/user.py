from pydantic import BaseModel, field_validator, model_validator, EmailStr, ConfigDict
from typing import Optional
from datetime import date
from uuid import UUID
import phonenumbers


class UserBase(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    second_name: Optional[str] = None


class UserCreate(UserBase):
    country_code: str
    number: str
    password: str
    phone_number: Optional[str] = None

    @field_validator("phone_number", mode="before", check_fields=False)
    def assemble_phone_number(cls, v, values):
        pass

    @model_validator(mode='after')
    def validate_phone(self) -> 'UserCreate':
        try:
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


class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Full user profile response"""
    id: UUID
    phone_number: str
    full_name: Optional[str] = None
    second_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    country_of_residence: Optional[str] = None
    home_address: Optional[str] = None
    town: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    address_country: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    current_password: Optional[str] = None  # Optional, not required for update
    
    # Updatable fields (all optional)
    full_name: Optional[str] = None
    second_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    country_of_residence: Optional[str] = None
    home_address: Optional[str] = None
    town: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    address_country: Optional[str] = None
    new_password: Optional[str] = None  # Optional password change
