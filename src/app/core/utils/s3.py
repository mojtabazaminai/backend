import boto3
from botocore.exceptions import ClientError

from ..config import settings

_client = None


def _is_configured() -> bool:
    return bool(settings.S3_BUCKET_NAME)


def _get_client():
    global _client
    if _client is None:
        kwargs = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        _client = boto3.client("s3", **kwargs)
    return _client


def get_s3_address(key: str | None) -> str | None:
    if not key or not _is_configured():
        return None
    base = settings.S3_ENDPOINT_URL.rstrip("/") if settings.S3_ENDPOINT_URL else "https://s3.amazonaws.com"
    return f"{base}/{settings.S3_BUCKET_NAME}/{key}"


def generate_presigned_url(key: str | None, expires_in: int = 600) -> str | None:
    if not key or not _is_configured():
        return None
    try:
        return _get_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    except (ClientError, Exception):
        return None
