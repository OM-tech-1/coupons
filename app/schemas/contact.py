from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class ContactMessageCreate(BaseModel):
    """Schema for creating a contact message"""
    name: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., min_length=5, max_length=150, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    subject: str = Field(..., min_length=5, max_length=255)
    message: str = Field(..., min_length=10)


class ContactMessageResponse(BaseModel):
    """Public response after submitting a message"""
    id: UUID
    name: str
    email: str
    subject: str
    message: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContactMessageAdminResponse(ContactMessageResponse):
    """Admin response with additional fields"""
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ContactMessageUpdate(BaseModel):
    """Schema for updating message status"""
    status: str = Field(..., pattern="^(pending|resolved)$")


class PaginatedContactMessagesResponse(BaseModel):
    """Paginated list of contact messages"""
    total: int
    items: list[ContactMessageAdminResponse]
    skip: int
    limit: int
