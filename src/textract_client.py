"""
Textract client for extracting text from PDF files stored in S3
Supports PII redaction via S3 Object Lambda
"""

import boto3
import json
import logging
import os
from botocore.exceptions import ClientError, BotoCoreError
from pdf_validator import PDFValidator

logger = logging.getLogger(__name__)


class TextractClient:
    def __init__(self):
        """Initialize Textract client"""
        self.textract = boto3.client("textract")
        self.s3 = boto3.client("s3")
        self.pdf_validator = PDFValidator()
        self.pii_access_point = os.environ.get("PII_REDACTED_ACCESS_POINT")
        
    def _get_s3_reference(self, bucket_name, s3_key, use_pii_redaction=True):
        """
        Get the appropriate S3 reference for Textract
        
        Args:
            bucket_name (str): Original S3 bucket name
            s3_key (str): S3 object key
            use_pii_redaction (bool): Whether to use PII redaction if available
            
        Returns:
            dict: S3 reference for Textract API
        """
        if use_pii_redaction and self.pii_access_point:
            logger.info(f"Using PII redaction access point for Textract: {s3_key}")
            return {"S3Object": {"Bucket": self.pii_access_point, "Name": s3_key}}
        else:
            logger.info(f"Using direct S3 access for Textract: s3://{bucket_name}/{s3_key}")
            return {"S3Object": {"Bucket": bucket_name, "Name": s3_key}}

    def extract_text_from_s3_pdf(self, bucket_name, s3_key, use_pii_redaction=False):
        """
        Extract text from a PDF file stored in S3 using Textract
        Note: PII redaction is disabled for PDF files to avoid Textract compatibility issues
        PII redaction should be applied to the extracted text instead

        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key for the PDF file
            use_pii_redaction (bool): Whether to use PII redaction (disabled for PDFs)

        Returns:
            dict: Contains 'success' boolean and either 'text' or 'error' message
        """
        try:
            # Validate file extension
            if not s3_key.lower().endswith(".pdf"):
                return {
                    "success": False,
                    "error": "Unsupported file format. Only PDF files are supported.",
                }

            # Check if file exists in S3
            try:
                self.s3.head_object(Bucket=bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return {"success": False, "error": "File not found in S3."}
                raise
            # Skip validation - let Textract handle everything
            logger.info(f"Processing PDF directly with Textract: s3://{bucket_name}/{s3_key}")

            # Call Textract to extract text
            logger.info(f"Starting text extraction for s3://{bucket_name}/{s3_key}")

            # Get appropriate S3 reference (with or without PII redaction)
            s3_document = self._get_s3_reference(bucket_name, s3_key, use_pii_redaction)
            
            # Try synchronous API first (for single-page PDFs and images)
            try:
                response = self.textract.detect_document_text(Document=s3_document)
                logger.info("Successfully used synchronous Textract API")
            except ClientError as textract_error:
                error_code = textract_error.response["Error"]["Code"]
                
                if error_code == "UnsupportedDocumentException":
                    logger.info("Synchronous API failed, trying asynchronous API for multi-page PDF")
                    # Try asynchronous API for multi-page PDFs
                    return self._extract_text_async(bucket_name, s3_key, use_pii_redaction)
                else:
                    # Re-raise other errors to be handled by outer exception handler
                    raise textract_error

            # Extract text from Textract response
            extracted_text = self._parse_textract_response(response)

            if not extracted_text.strip():
                return {
                    "success": False,
                    "error": "No text could be extracted from the PDF. The file may be corrupted or password-protected.",
                }

            logger.info(
                f"Successfully extracted {len(extracted_text)} characters from PDF"
            )

            return {"success": True, "text": extracted_text}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "InvalidS3ObjectException":
                return {
                    "success": False,
                    "error": "Invalid PDF file. The file may be corrupted or password-protected.",
                }
            elif error_code == "UnsupportedDocumentException":
                # Get more details about the PDF for better error reporting
                file_info = self.pdf_validator.get_detailed_file_info(bucket_name, s3_key)
                
                # Log the full error for debugging
                logger.error(f"Textract UnsupportedDocumentException for {s3_key}: {e}")
                logger.error(f"File info: {file_info}")
                
                # Try to give more specific guidance
                suggestions = []
                if file_info.get('size_mb', 0) > 5:
                    suggestions.append("Try reducing the file size")
                if file_info.get('content_type') != 'application/pdf':
                    suggestions.append("Ensure the file is saved as a proper PDF")
                
                suggestions.extend([
                    "Try re-saving the PDF from the original application",
                    "Convert to PDF/A format if possible",
                    "Remove any password protection or encryption"
                ])
                
                return {
                    "success": False,
                    "error": f"Textract cannot process this PDF format. File: {file_info.get('size_mb', 0)}MB, Type: {file_info.get('content_type', 'unknown')}",
                    "suggestion": "Try: " + " | ".join(suggestions[:3]),
                    "file_info": file_info,
                    "textract_error": str(e)
                }
            elif error_code == "AccessDenied":
                return {
                    "success": False,
                    "error": "Access denied to S3 object or Textract service.",
                }
            else:
                logger.error(f"Textract ClientError: {error_code} - {e}")
                return {
                    "success": False,
                    "error": "PDF processing failed due to service error.",
                }

        except BotoCoreError as e:
            logger.error(f"Textract BotoCoreError: {e}")
            return {
                "success": False,
                "error": "PDF processing failed due to connection error.",
            }

        except Exception as e:
            logger.error(f"Unexpected error during text extraction: {e}")
            return {
                "success": False,
                "error": "PDF processing failed due to unexpected error.",
            }

    def _parse_textract_response(self, response):
        """
        Parse Textract response and extract text content

        Args:
            response (dict): Textract detect_document_text response

        Returns:
            str: Extracted text content
        """
        text_blocks = []

        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                text_blocks.append(block["Text"])

        return "\n".join(text_blocks)

    def _extract_text_async(self, bucket_name, s3_key, use_pii_redaction=True):
        """
        Extract text using asynchronous Textract API for multi-page PDFs
        Optionally applies PII redaction via S3 Object Lambda
        
        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key for the PDF file
            use_pii_redaction (bool): Whether to use PII redaction if available
            
        Returns:
            dict: Contains 'success' boolean and either 'text' or 'error' message
        """
        import time
        
        try:
            logger.info(f"Starting asynchronous text extraction for s3://{bucket_name}/{s3_key}")
            
            # Log the current AWS region and credentials info for debugging
            logger.info(f"Textract client region: {self.textract.meta.region_name}")
            
            # Get appropriate S3 reference (with or without PII redaction)
            s3_document_location = self._get_s3_reference(bucket_name, s3_key, use_pii_redaction)
            
            # Start the asynchronous job
            logger.info("Calling start_document_text_detection...")
            response = self.textract.start_document_text_detection(
                DocumentLocation=s3_document_location
            )
            
            job_id = response['JobId']
            logger.info(f"Started Textract job: {job_id}")
            
            # Poll for completion (with timeout)
            max_wait_time = 300  # 5 minutes max
            poll_interval = 5    # Check every 5 seconds
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                
                # Check job status
                status_response = self.textract.get_document_text_detection(JobId=job_id)
                job_status = status_response['JobStatus']
                
                logger.info(f"Job {job_id} status: {job_status} (elapsed: {elapsed_time}s)")
                
                if job_status == 'SUCCEEDED':
                    # Extract text from all pages
                    extracted_text = self._parse_async_textract_response(job_id)
                    
                    if not extracted_text.strip():
                        return {
                            "success": False,
                            "error": "No text could be extracted from the PDF. The file may be corrupted or password-protected.",
                        }
                    
                    logger.info(f"Successfully extracted {len(extracted_text)} characters from multi-page PDF")
                    return {"success": True, "text": extracted_text}
                    
                elif job_status == 'FAILED':
                    status_message = status_response.get('StatusMessage', 'Unknown error')
                    return {
                        "success": False,
                        "error": f"Textract job failed: {status_message}",
                    }
                elif job_status in ['IN_PROGRESS', 'PARTIAL_SUCCESS']:
                    # Continue polling
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Unexpected job status: {job_status}",
                    }
            
            # Timeout reached
            return {
                "success": False,
                "error": f"Textract job timed out after {max_wait_time} seconds. Large PDFs may take longer to process.",
            }
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Async Textract ClientError: {error_code} - {error_message}")
            logger.error(f"Full error response: {e.response}")
            
            if error_code == "AccessDeniedException":
                logger.error(f"AccessDenied details - Bucket: {bucket_name}, Key: {s3_key}")
                logger.error(f"Current IAM role should have permissions for: start_document_text_detection, get_document_text_detection")
                return {
                    "success": False,
                    "error": f"Access denied to Textract async API. Error: {error_message}",
                    "suggestion": "Check IAM permissions for start_document_text_detection and get_document_text_detection",
                }
            elif error_code == "InvalidS3ObjectException":
                return {
                    "success": False,
                    "error": "Invalid PDF file. The file may be corrupted or password-protected.",
                }
            elif error_code == "UnsupportedDocumentException":
                return {
                    "success": False,
                    "error": "PDF format not supported by Textract. Try converting to a standard PDF format.",
                }
            else:
                return {
                    "success": False,
                    "error": f"Textract service error: {error_code} - {error_message}",
                }
                
        except Exception as e:
            logger.error(f"Unexpected error in async text extraction: {e}")
            return {
                "success": False,
                "error": "PDF processing failed due to unexpected error.",
            }

    def _parse_async_textract_response(self, job_id):
        """
        Parse asynchronous Textract response and extract text content from all pages
        
        Args:
            job_id (str): Textract job ID
            
        Returns:
            str: Extracted text content from all pages
        """
        text_blocks = []
        next_token = None
        
        try:
            while True:
                # Get results (with pagination)
                if next_token:
                    response = self.textract.get_document_text_detection(
                        JobId=job_id,
                        NextToken=next_token
                    )
                else:
                    response = self.textract.get_document_text_detection(JobId=job_id)
                
                # Extract text from this batch
                for block in response.get("Blocks", []):
                    if block["BlockType"] == "LINE":
                        text_blocks.append(block["Text"])
                
                # Check if there are more pages
                next_token = response.get('NextToken')
                if not next_token:
                    break
                    
                logger.info(f"Processing next page batch for job {job_id}")
                
        except Exception as e:
            logger.error(f"Error parsing async Textract response: {e}")
            # Return what we have so far
            pass
        
        return "\n".join(text_blocks)

    def validate_pdf_file(self, bucket_name, s3_key):
        """
        Validate that the S3 object is a valid PDF file

        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key

        Returns:
            dict: Contains 'valid' boolean and 'error' message if invalid
        """
        try:
            # Check file extension
            if not s3_key.lower().endswith(".pdf"):
                return {"valid": False, "error": "File must have .pdf extension"}

            # Get object metadata
            response = self.s3.head_object(Bucket=bucket_name, Key=s3_key)

            # Check content type if available
            content_type = response.get("ContentType", "")
            if content_type and not content_type.startswith("application/pdf"):
                return {"valid": False, "error": "File content type is not PDF"}

            # Check file size (Textract has limits)
            content_length = response.get("ContentLength", 0)
            if (
                content_length > 10 * 1024 * 1024
            ):  # 10MB limit for synchronous processing
                return {
                    "valid": False,
                    "error": "PDF file is too large (max 10MB for processing)",
                }

            if content_length == 0:
                return {"valid": False, "error": "PDF file is empty"}

            return {"valid": True}

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return {"valid": False, "error": "File not found in S3"}
            return {
                "valid": False,
                "error": f'Error accessing file: {e.response["Error"]["Message"]}',
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Unexpected error validating file: {str(e)}",
            }
