
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from app.services.s3_service import S3Service
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/upload/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image to S3. 
    Only admins can upload coupon images.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload images"
        )
    
    url = await S3Service.upload_file(file)
    return {"url": url}
