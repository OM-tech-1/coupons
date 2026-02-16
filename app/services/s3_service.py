
import boto3
import os
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from typing import Optional
import uuid

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
            # print(f"Error creating S3 client: {e}")
            return None

    @staticmethod
    async def upload_file(file: UploadFile, folder: str = "uploads") -> str:
        """
        Upload a file to S3 and return the public URL.
        """
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Validate file type (only images)
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
            
        # Check file size (e.g., max 5MB) - manually reading chunk size or just trusting configured limit
        # Here we proceed with upload. content-length might not be set.

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
        
        # Determine prefix
        env_prefix = os.getenv('S3_PREFIX', 'coupons')
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"{env_prefix}/{unique_filename}"

        try:
            # Upload file
            # We use upload_fileobj for stream upload
            s3_client.upload_fileobj(
                file.file,
                bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": file.content_type,
                    # "ACL": "public-read" # Use if bucket is public, or reliance on bucket policy
                }
            )
            
            # Construct URL
            # Assuming standard S3 URL format or CloudFront if configured. 
            # For now, standard S3 URL.
            region = os.getenv('AWS_REGION')
            url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
            
            return url

        except ClientError as e:
            # print(f"S3 Upload Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image"
            )
        except Exception as e:
            # print(f"Upload Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during upload"
            )
