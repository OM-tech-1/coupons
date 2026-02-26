from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.contact import (
    ContactMessageCreate,
    ContactMessageResponse,
    ContactMessageAdminResponse,
    ContactMessageUpdate,
    PaginatedContactMessagesResponse
)
from app.models.contact_message import ContactMessage
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
def submit_contact_message(
    data: ContactMessageCreate,
    db: Session = Depends(get_db)
):
    """Submit a new contact/support message (public endpoint)"""
    message = ContactMessage(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message,
        status="pending"
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message


@router.get("/admin", response_model=PaginatedContactMessagesResponse)
def list_contact_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|resolved)$"),
    search: Optional[str] = Query(None, description="Search by name, email, or subject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all contact messages (Admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(ContactMessage)
    
    # Apply filters
    if status_filter:
        query = query.filter(ContactMessage.status == status_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (ContactMessage.name.ilike(search_pattern)) |
            (ContactMessage.email.ilike(search_pattern)) |
            (ContactMessage.subject.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    messages = query.order_by(ContactMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    return PaginatedContactMessagesResponse(
        total=total,
        items=messages,
        skip=skip,
        limit=limit
    )


@router.get("/admin/{message_id}", response_model=ContactMessageAdminResponse)
def get_contact_message(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific contact message (Admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message


@router.patch("/admin/{message_id}", response_model=ContactMessageAdminResponse)
def update_contact_message_status(
    message_id: UUID,
    data: ContactMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update contact message status (Admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    message.status = data.status
    db.commit()
    db.refresh(message)
    
    return message
