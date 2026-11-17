import io
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image

ALLOWED_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {"image/webp", "image/png", "image/jpeg", "image/jpg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# In-memory presigned URL cache to avoid recalculating signatures repeatedly
# Format: {object_key: (url, expiry_timestamp)}
_PRESIGNED_CACHE: Dict[str, Tuple[str, float]] = {}


class NeonStorageService:
    """Neon Object Storage (S3-compatible) service for UI template preview images."""

    def __init__(self):
        self._s3_client = None

    def _get_config(self):
        bucket = os.getenv("NEON_STORAGE_BUCKET", "photos")
        endpoint_url = os.getenv("AWS_ENDPOINT_URL_S3", "").strip()
        region_name = os.getenv("AWS_REGION", "ap-southeast-1").strip()
        access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
        return bucket, endpoint_url, region_name, access_key, secret_key

    @property
    def bucket(self):
        return os.getenv("NEON_STORAGE_BUCKET", "photos")

    def get_client(self):
        """Returns lazy-initialized boto3 S3 client configured with SigV4."""
        if self._s3_client is None:
            bucket, endpoint_url, region_name, access_key, secret_key = self._get_config()
            if not endpoint_url or not access_key or not secret_key:
                # Try reloading dotenv in case it was loaded after import
                from dotenv import load_dotenv
                load_dotenv()
                bucket, endpoint_url, region_name, access_key, secret_key = self._get_config()

            if not endpoint_url or not access_key or not secret_key:
                raise ValueError("Neon Object Storage credentials not fully configured in environment.")

            config = Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=10,
                read_timeout=30,
            )
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name=region_name,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=config,
            )
        return self._s3_client

    def validate_image_bytes(self, image_bytes: bytes, filename: str = "upload.webp") -> Tuple[int, int, str]:
        """Validates file size, extension and PIL readability. Returns (width, height, format)."""
        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB.")

        ext = Path(filename).suffix.lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
            # Reopen to read dimensions since verify() mutates the stream
            with Image.open(io.BytesIO(image_bytes)) as img:
                return img.width, img.height, img.format or "WEBP"
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image content: {e}")

    def optimize_image(
        self,
        image_bytes: bytes,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        quality: int = 88,
    ) -> Tuple[bytes, int, int]:
        """
        Optimizes and converts image to WebP format, optionally resizing to target dimensions.
        Returns (optimized_bytes, width, height).
        """
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert modes like RGBA or P to RGB or RGBA cleanly
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                canvas = img.convert("RGBA")
            else:
                canvas = img.convert("RGB")

            orig_w, orig_h = canvas.size

            if target_width and target_height:
                # Resize with aspect ratio preserved, fitting within target box
                canvas.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
            elif target_width and not target_height:
                ratio = target_width / float(orig_w)
                new_h = int(orig_h * ratio)
                canvas = canvas.resize((target_width, new_h), Image.Resampling.LANCZOS)
            elif target_height and not target_width:
                ratio = target_height / float(orig_h)
                new_w = int(orig_w * ratio)
                canvas = canvas.resize((new_w, target_height), Image.Resampling.LANCZOS)

            final_w, final_h = canvas.size
            output_io = io.BytesIO()
            canvas.save(output_io, format="WEBP", quality=quality, method=6)
            return output_io.getvalue(), final_w, final_h

    def upload_bytes(
        self,
        image_bytes: bytes,
        object_key: str,
        content_type: str = "image/webp",
    ) -> Dict[str, Any]:
        """Uploads raw image bytes to Neon Object Storage and returns object metadata."""
        width, height, _ = self.validate_image_bytes(image_bytes, filename=object_key)
        client = self.get_client()

        try:
            client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=image_bytes,
                ContentType=content_type,
            )
            # Invalidate any cached presigned URL for this key
            _PRESIGNED_CACHE.pop(object_key, None)

            return {
                "bucket_name": self.bucket,
                "object_key": object_key,
                "content_type": content_type,
                "file_size": len(image_bytes),
                "width": width,
                "height": height,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
        except ClientError as e:
            raise RuntimeError(f"Neon S3 upload failed for key '{object_key}': {e}")

    def upload_file(
        self,
        file_path_or_bytes: Any,
        object_key: str,
        optimize: bool = True,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Uploads a file or bytes with optional optimization to WebP."""
        if isinstance(file_path_or_bytes, (str, Path)):
            with open(file_path_or_bytes, "rb") as f:
                raw_bytes = f.read()
        elif hasattr(file_path_or_bytes, "read"):
            raw_bytes = file_path_or_bytes.read()
        elif isinstance(file_path_or_bytes, bytes):
            raw_bytes = file_path_or_bytes
        else:
            raise ValueError("Unsupported file input type")

        if optimize:
            data, w, h = self.optimize_image(
                raw_bytes,
                target_width=target_width,
                target_height=target_height,
            )
            content_type = "image/webp"
            if not object_key.endswith(".webp"):
                object_key = f"{Path(object_key).stem}.webp"
        else:
            data = raw_bytes
            w, h, fmt = self.validate_image_bytes(data, filename=object_key)
            content_type = f"image/{fmt.lower()}"

        client = self.get_client()
        client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        _PRESIGNED_CACHE.pop(object_key, None)

        return {
            "bucket_name": self.bucket,
            "object_key": object_key,
            "content_type": content_type,
            "file_size": len(data),
            "width": w,
            "height": h,
        }

    def check_object_exists(self, object_key: str) -> bool:
        """Checks if an object exists in the bucket."""
        client = self.get_client()
        try:
            client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise RuntimeError(f"Error checking object '{object_key}': {e}")

    def get_object_metadata(self, object_key: str) -> Dict[str, Any]:
        """Retrieves metadata of an existing object in Neon storage."""
        client = self.get_client()
        try:
            res = client.head_object(Bucket=self.bucket, Key=object_key)
            return {
                "content_length": res.get("ContentLength"),
                "content_type": res.get("ContentType"),
                "etag": res.get("ETag"),
                "last_modified": res.get("LastModified"),
            }
        except ClientError as e:
            raise RuntimeError(f"Failed to retrieve metadata for '{object_key}': {e}")

    def delete_object(self, object_key: str) -> bool:
        """Deletes an object from Neon storage."""
        client = self.get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=object_key)
            _PRESIGNED_CACHE.pop(object_key, None)
            return True
        except ClientError as e:
            raise RuntimeError(f"Failed to delete object '{object_key}': {e}")

    def list_objects(self, prefix: str = "", max_keys: int = 100) -> list:
        """Lists objects from the Neon Object Storage bucket under prefix."""
        client = self.get_client()
        try:
            res = client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, MaxKeys=max_keys)
            items = []
            for obj in res.get("Contents", []):
                items.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat() if hasattr(obj["LastModified"], "isoformat") else str(obj["LastModified"]),
                    "etag": obj.get("ETag", "").strip('"'),
                })
            return items
        except Exception as e:
            # If S3 call fails (e.g. offline/mocked), return empty list gracefully
            return []

    def generate_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Generates a secure, short-lived presigned GET URL with SigV4 for the private bucket.
        Caches URLs until 5 minutes before expiration to avoid repeated signature calculations.
        """
        now = time.time()
        cached = _PRESIGNED_CACHE.get(object_key)
        if cached:
            url, expiry = cached
            if now < expiry:
                return url

        client = self.get_client()
        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expires_in,
            )
            # Store in cache with safety margin of 300 seconds (5 min)
            _PRESIGNED_CACHE[object_key] = (url, now + max(60, expires_in - 300))
            return url
        except ClientError as e:
            raise RuntimeError(f"Failed to generate presigned URL for '{object_key}': {e}")


# Singleton service instance
storage_service = NeonStorageService()
