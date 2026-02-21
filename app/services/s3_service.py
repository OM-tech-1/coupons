
import boto3
import os
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from typing import Optional
import uuid
import io

# Safe image extensions allowlist
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

class S3Service:
    @staticmethod
    def get_s3_client():
        try:
            return boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
        except Exception as e:
            return None

    @staticmethod
    async def upload_file(file: UploadFile, folder: str = "uploads") -> str:
        """
        Upload a file to S3 and return the public URL.
        """
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Validate file type by content_type (client-sent, first check)
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Validate file extension (server-side, not client-controlled)
        file_extension = os.path.splitext(file.filename or "")[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{file_extension}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Read file with size limit enforcement
        chunks = []
        total_size = 0
        while True:
            chunk = await file.read(64 * 1024)  # 64KB chunks
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB"
                )
            chunks.append(chunk)
        
        file_bytes = b"".join(chunks)

        s3_client = S3Service.get_s3_client()
        if not s3_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Storage service unavailable"
            )

        bucket_name = os.getenv('S3_BUCKET_NAME')
        if not bucket_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: Bucket name missing"
            )
        
        env_prefix = os.getenv('S3_PREFIX', 'coupons')
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"{env_prefix}/{unique_filename}"

        try:
            s3_client.upload_fileobj(
                io.BytesIO(file_bytes),
                bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": file.content_type,
                }
            )
            
            region = os.getenv('AWS_REGION')
            url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            return url

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during upload"
            )

