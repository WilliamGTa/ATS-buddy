"""
Deduplication service for resume processing.
Handles file hash calculation, cache lookup, and deduplication logic.
"""

import logging
from typing import Dict, Any, Optional
from file_hash_utils import calculate_s3_file_hash
from dynamodb_client import DynamoDBClient
import boto3

logger = logging.getLogger(__name__)


class DeduplicationService:
    """Service for handling resume file deduplication."""
    
    def __init__(self):
        """Initialize deduplication service with required clients."""
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = DynamoDBClient()
    
    def check_file_deduplication(self, bucket_name: str, s3_key: str, original_filename: str = None) -> Dict[str, Any]:
        """
        Check if a file has been processed before and handle deduplication.
        
        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            original_filename: Original filename (optional, defaults to s3_key basename)
            
        Returns:
            Dict containing:
                - is_duplicate: bool indicating if file is a duplicate
                - file_hash: str SHA-256 hash of the file
                - cached_data: dict with cached resume data if duplicate
                - message: str status message
        """
        try:
            # Use original filename or extract from s3_key
            filename = original_filename or s3_key.split('/')[-1]
            
            # Calculate file hash
            logger.info(f"Calculating hash for file: s3://{bucket_name}/{s3_key}")
            file_hash = calculate_s3_file_hash(self.s3_client, bucket_name, s3_key)
            
            if not file_hash:
                return {
                    "is_duplicate": False,
                    "file_hash": None,
                    "cached_data": None,
                    "message": "Failed to calculate file hash",
                    "error": "Hash calculation failed"
                }
            
            # Check cache for existing hash
            logger.info(f"Checking cache for hash: {file_hash[:8]}...")
            cached_data = self.dynamodb_client.get_resume_cache(file_hash)
            
            if cached_data:
                logger.info(f"File is a duplicate - using cached data for: {cached_data['original_filename']}")
                return {
                    "is_duplicate": True,
                    "file_hash": file_hash,
                    "cached_data": cached_data,
                    "message": f"Resume already processed - using existing data from {cached_data['original_filename']}"
                }
            else:
                logger.info(f"File is unique - proceeding with processing")
                return {
                    "is_duplicate": False,
                    "file_hash": file_hash,
                    "cached_data": None,
                    "message": "File is unique - proceeding with processing"
                }
                
        except Exception as e:
            logger.error(f"Error in deduplication check: {e}")
            return {
                "is_duplicate": False,
                "file_hash": None,
                "cached_data": None,
                "message": "Deduplication check failed - proceeding with processing",
                "error": str(e)
            }
    
    def store_processed_file(self, file_hash: str, extracted_text: str, original_filename: str) -> bool:
        """
        Store processed file data in cache.
        
        Args:
            file_hash: SHA-256 hash of the file
            extracted_text: Extracted text from the file
            original_filename: Original filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.dynamodb_client.put_resume_cache(
                file_hash=file_hash,
                extracted_text=extracted_text,
                original_filename=original_filename
            )
            
            if success:
                logger.info(f"Successfully cached processed file: {original_filename}")
            else:
                logger.warning(f"Failed to cache processed file: {original_filename}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing processed file in cache: {e}")
            return False