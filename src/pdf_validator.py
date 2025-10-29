"""
Enhanced PDF validation utilities for ATS Buddy
"""

import boto3
import io
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PDFValidator:
    def __init__(self):
        self.s3 = boto3.client('s3')
    
    def validate_pdf_structure(self, bucket_name, s3_key):
        """
        Validate PDF structure by checking file headers and basic format
        
        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key
            
        Returns:
            dict: Validation result with detailed information
        """
        try:
            # Download first 2KB to check PDF header more thoroughly
            response = self.s3.get_object(
                Bucket=bucket_name, 
                Key=s3_key,
                Range='bytes=0-2047'
            )
            
            header_data = response['Body'].read()
            
            # Check PDF magic number - this is critical
            if not header_data.startswith(b'%PDF-'):
                return {
                    'valid': False,
                    'critical': True,
                    'error': 'File does not have valid PDF header',
                    'suggestion': 'Ensure the file is a valid PDF document'
                }
            
            # Extract PDF version
            pdf_version = header_data[:8].decode('ascii', errors='ignore')
            logger.info(f"PDF version detected: {pdf_version}")
            
            # Check for explicit password protection - be more specific
            # Look for actual encryption dictionary, not just the word "encrypt"
            has_encrypt_dict = b'/Encrypt ' in header_data or b'/Encrypt\n' in header_data or b'/Encrypt\r' in header_data
            
            if has_encrypt_dict:
                return {
                    'valid': False,
                    'critical': True,
                    'error': 'PDF is password-protected or encrypted',
                    'suggestion': 'Remove password protection from the PDF before processing'
                }
            
            # Warn about potential issues but don't block processing
            warnings = []
            if b'xref' not in header_data.lower() and b'/XRef' not in header_data:
                warnings.append("No xref table found in header - may be a linearized PDF")
            
            if warnings:
                logger.info(f"PDF validation warnings: {'; '.join(warnings)}")
            
            return {
                'valid': True,
                'critical': False,
                'pdf_version': pdf_version,
                'warnings': warnings,
                'info': 'PDF structure appears valid'
            }
            
        except ClientError as e:
            return {
                'valid': False,
                'critical': True,
                'error': f'Cannot access PDF file: {e.response["Error"]["Message"]}',
                'suggestion': 'Check file permissions and bucket access'
            }
        except Exception as e:
            # Don't fail validation on unexpected errors - let Textract try
            logger.warning(f"PDF validation encountered error but proceeding: {str(e)}")
            return {
                'valid': True,
                'critical': False,
                'error': f'Validation warning: {str(e)}',
                'suggestion': 'PDF structure check incomplete but proceeding with processing'
            }
    
    def get_detailed_file_info(self, bucket_name, s3_key):
        """
        Get detailed information about the S3 file
        
        Args:
            bucket_name (str): S3 bucket name  
            s3_key (str): S3 object key
            
        Returns:
            dict: Detailed file information
        """
        try:
            response = self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            
            return {
                'size_bytes': response.get('ContentLength', 0),
                'size_mb': round(response.get('ContentLength', 0) / (1024 * 1024), 2),
                'content_type': response.get('ContentType', 'Unknown'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            return {'error': f'Cannot get file info: {str(e)}'}