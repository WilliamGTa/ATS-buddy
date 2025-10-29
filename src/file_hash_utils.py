"""
File hash utilities for resume deduplication.
Provides SHA-256 hashing functionality for PDF content.
"""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        str: SHA-256 hash as hexadecimal string
        
    Raises:
        ValueError: If file_content is None or empty
    """
    if not file_content:
        raise ValueError("File content cannot be None or empty")
    
    try:
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        hash_value = sha256_hash.hexdigest()
        
        logger.info(f"Calculated file hash: {hash_value[:8]}... (length: {len(file_content)} bytes)")
        return hash_value
        
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        raise


def calculate_s3_file_hash(s3_client, bucket_name: str, s3_key: str) -> Optional[str]:
    """
    Calculate SHA-256 hash of a file stored in S3.
    
    Args:
        s3_client: Boto3 S3 client instance
        bucket_name: S3 bucket name
        s3_key: S3 object key
        
    Returns:
        str: SHA-256 hash as hexadecimal string, or None if error
    """
    try:
        # Download file content from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        file_content = response['Body'].read()
        
        return calculate_file_hash(file_content)
        
    except Exception as e:
        logger.error(f"Error calculating S3 file hash for s3://{bucket_name}/{s3_key}: {e}")
        return None