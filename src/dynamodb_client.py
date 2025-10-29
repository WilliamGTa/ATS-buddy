"""
DynamoDB client wrapper for resume cache operations.
Provides basic put and get operations for the resume cache table.
"""

import boto3
import os
import time
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class DynamoDBClient:
    """DynamoDB client wrapper for resume cache operations."""
    
    def __init__(self):
        """Initialize DynamoDB client with table name from environment."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.environ.get('RESUME_CACHE_TABLE')
        if not self.table_name:
            raise ValueError("RESUME_CACHE_TABLE environment variable not set")
        self.table = self.dynamodb.Table(self.table_name)
    
    def put_resume_cache(self, file_hash: str, extracted_text: str, original_filename: str, ttl_hours: int = 12) -> bool:
        """
        Store resume cache data in DynamoDB.
        
        Args:
            file_hash: SHA-256 hash of the file content
            extracted_text: Text extracted from the resume
            original_filename: Original filename of the uploaded file
            ttl_hours: Number of hours before the item expires (default: 12)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Calculate TTL timestamp (current time + ttl_hours)
            ttl_timestamp = int(time.time()) + (ttl_hours * 60 * 60)
            
            item = {
                'file_hash': file_hash,
                'extracted_text': extracted_text,
                'original_filename': original_filename,
                'ttl': ttl_timestamp
            }
            
            self.table.put_item(Item=item)
            logger.info(f"Successfully stored resume cache for hash: {file_hash[:8]}...")
            return True
            
        except ClientError as e:
            logger.error(f"Error storing resume cache: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing resume cache: {e}")
            return False
    
    def get_resume_cache(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve resume cache data from DynamoDB.
        
        Args:
            file_hash: SHA-256 hash of the file content
            
        Returns:
            Dict containing cache data if found, None otherwise
        """
        try:
            response = self.table.get_item(
                Key={'file_hash': file_hash}
            )
            
            if 'Item' in response:
                item = response['Item']
                logger.info(f"Found cached resume for hash: {file_hash[:8]}...")
                return {
                    'file_hash': item['file_hash'],
                    'extracted_text': item['extracted_text'],
                    'original_filename': item['original_filename'],
                    'ttl': item['ttl']
                }
            else:
                logger.info(f"No cached resume found for hash: {file_hash[:8]}...")
                return None
                
        except ClientError as e:
            logger.error(f"Error retrieving resume cache: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving resume cache: {e}")
            return None
    
    def cache_exists(self, file_hash: str) -> bool:
        """
        Check if a resume cache exists for the given file hash.
        
        Args:
            file_hash: SHA-256 hash of the file content
            
        Returns:
            bool: True if cache exists, False otherwise
        """
        cache_data = self.get_resume_cache(file_hash)
        return cache_data is not None