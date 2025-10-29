"""
Test suite for S3Handler functionality
"""
import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from s3_handler import S3Handler

class TestS3Handler:
    @patch("s3_handler.boto3.client")
    def test_handle_s3_upload_event_success(self, mock_boto3):
        """Test successful S3 upload event handling"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "resumes/test.pdf"},
                    }
                }
            ]
        }
        handler = S3Handler()
        result = handler.handle_s3_upload_event(event)
        assert result["success"] is True
        assert result["bucket_name"] == "test-bucket"
        assert result["s3_key"] == "resumes/test.pdf"

    @patch("s3_handler.boto3.client")
    def test_handle_s3_upload_event_no_records(self, mock_boto3):
        """Test S3 event with no Records"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        event = {}
        handler = S3Handler()
        result = handler.handle_s3_upload_event(event)
        assert result["success"] is False
        assert "no Records found" in result["error"]

    @patch("s3_handler.boto3.client")
    def test_handle_s3_upload_event_missing_s3_info(self, mock_boto3):
        """Test S3 event with missing s3 information"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        event = {"Records": [{"eventName": "s3:ObjectCreated:Put"}]}
        handler = S3Handler()
        result = handler.handle_s3_upload_event(event)
        assert result["success"] is False
        assert "no S3 information found" in result["error"]

    @patch("s3_handler.boto3.client")
    def test_get_file_info_success(self, mock_boto3):
        """Test successful file info retrieval"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        mock_s3.head_object.return_value = {
            "ContentLength": 1024,
            "ContentType": "application/pdf",
            "LastModified": "2024-01-01T00:00:00Z",
            "ETag": '"abc123"',
        }
        handler = S3Handler()  # Create handler after patching
        result = handler.get_file_info("test-bucket", "test.pdf")
        assert result["success"] is True
        assert result["size"] == 1024
        assert result["content_type"] == "application/pdf"
        assert result["etag"] == "abc123"

    @patch("s3_handler.boto3.client")
    def test_get_file_info_not_found(self, mock_boto3):
        """Test file not found error"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        error_response = {"Error": {"Code": "404"}}
        mock_s3.head_object.side_effect = ClientError(error_response, "HeadObject")
        handler = S3Handler()  # Create handler after patching
        result = handler.get_file_info("test-bucket", "nonexistent.pdf")
        assert result["success"] is False
        assert "File not found" in result["error"]

    @patch("s3_handler.boto3.client")
    def test_get_file_info_access_denied(self, mock_boto3):
        """Test access denied error"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3.head_object.side_effect = ClientError(error_response, "HeadObject")
        handler = S3Handler()  # Create handler after patching
        result = handler.get_file_info("test-bucket", "test.pdf")
        assert result["success"] is False
        assert "Access denied" in result["error"]

    @patch("s3_handler.boto3.client")
    def test_create_presigned_url_success(self, mock_boto3):
        """Test successful presigned URL generation"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        expected_url = "https://test-bucket.s3.amazonaws.com/test.pdf?presigned-params"
        mock_s3.generate_presigned_url.return_value = expected_url
        handler = S3Handler()  # Create handler after patching
        result = handler.create_presigned_url("test-bucket", "test.pdf", 3600)
        assert result["success"] is True
        assert result["url"] == expected_url
        assert result["expires_in"] == 3600

    @patch("s3_handler.boto3.client")
    def test_create_presigned_url_error(self, mock_boto3):
        """Test presigned URL generation error"""
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        mock_s3.generate_presigned_url.side_effect = Exception("AWS Error")
        handler = S3Handler()  # Create handler after patching
        result = handler.create_presigned_url("test-bucket", "test.pdf")
        assert result["success"] is False
        assert "Unexpected error" in result["error"]

if __name__ == "__main__":
    # Run basic tests
    print("Running S3Handler tests...")
    handler = S3Handler()
    print(f"✓ S3Handler initialized")
    # Test event parsing
    valid_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "test.pdf"},
                }
            }
        ]
    }
    result = handler.handle_s3_upload_event(valid_event)
    if result["success"]:
        print("✓ S3 event parsing works correctly")
        print(f"  - Bucket: {result['bucket_name']}")
        print(f"  - Key: {result['s3_key']}")
    else:
        print(f"✗ S3 event parsing failed: {result['error']}")
    # Test invalid event
    invalid_result = handler.handle_s3_upload_event({})
    if not invalid_result["success"]:
        print("✓ Invalid event handling works correctly")
    else:
        print("✗ Invalid event should have failed")
    print("\nS3Handler tests completed!")
