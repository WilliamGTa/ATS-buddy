"""
S3 handler for managing PDF uploads and file operations
"""

import boto3
import logging
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class S3Handler:
    def __init__(self):
        """Initialize S3 client"""
        self.s3 = boto3.client("s3")

    def handle_s3_upload_event(self, event):
        """
        Process S3 upload event from Lambda trigger

        Args:
            event (dict): Lambda event containing S3 upload information

        Returns:
            dict: Contains bucket name, key, and validation results
        """
        try:
            # Extract S3 information from event
            if "Records" not in event:
                return {
                    "success": False,
                    "error": "Invalid event format - no Records found",
                }

            # Get first record (assuming single file upload)
            record = event["Records"][0]

            if "s3" not in record:
                return {
                    "success": False,
                    "error": "Invalid event format - no S3 information found",
                }

            bucket_name = record["s3"]["bucket"]["name"]
            s3_key = record["s3"]["object"]["key"]

            logger.info(f"Processing S3 upload: s3://{bucket_name}/{s3_key}")

            return {"success": True, "bucket_name": bucket_name, "s3_key": s3_key}

        except KeyError as e:
            logger.error(f"Missing key in S3 event: {e}")
            return {
                "success": False,
                "error": f"Invalid S3 event structure: missing {e}",
            }
        except Exception as e:
            logger.error(f"Error processing S3 event: {e}")
            return {"success": False, "error": "Failed to process S3 upload event"}

    def get_file_info(self, bucket_name, s3_key):
        """
        Get information about a file in S3

        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key

        Returns:
            dict: File information or error details
        """
        try:
            response = self.s3.head_object(Bucket=bucket_name, Key=s3_key)

            return {
                "success": True,
                "size": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", ""),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag", "").strip('"'),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "404":
                return {"success": False, "error": "File not found in S3"}
            elif error_code == "AccessDenied":
                return {"success": False, "error": "Access denied to S3 object"}
            else:
                logger.error(f"S3 ClientError: {error_code} - {e}")
                return {"success": False, "error": "Failed to access file information"}

        except Exception as e:
            logger.error(f"Unexpected error getting file info: {e}")
            return {"success": False, "error": "Unexpected error accessing file"}

    def create_presigned_url(self, bucket_name, s3_key, expiration=3600):
        """
        Generate a presigned URL for downloading a file from S3

        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key
            expiration (int): URL expiration time in seconds (default: 1 hour)

        Returns:
            dict: Contains presigned URL or error details
        """
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )

            return {"success": True, "url": url, "expires_in": expiration}

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return {"success": False, "error": "Failed to generate download URL"}
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return {
                "success": False,
                "error": "Unexpected error generating download URL",
            }

    def upload_file_content(self, bucket_name, s3_key, file_content, content_type="application/octet-stream"):
        """
        Upload file content directly to S3

        Args:
            bucket_name (str): S3 bucket name
            s3_key (str): S3 object key
            file_content (bytes): File content to upload
            content_type (str): MIME type of the file

        Returns:
            dict: Upload result with success status
        """
        try:
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )

            logger.info(f"Successfully uploaded file to s3://{bucket_name}/{s3_key}")
            return {
                "success": True,
                "bucket_name": bucket_name,
                "s3_key": s3_key,
                "size": len(file_content)
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"S3 ClientError during upload: {error_code} - {e}")
            return {"success": False, "error": f"Failed to upload file: {error_code}"}
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            return {"success": False, "error": "Unexpected error during file upload"}
