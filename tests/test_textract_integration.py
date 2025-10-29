#!/usr/bin/env python3
"""
Test script for S3 and Textract integration
Tests various scenarios including error cases
"""
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from textract_client import TextractClient
from s3_handler import S3Handler
from handler import lambda_handler, handle_direct_invocation, handle_s3_upload

def test_textract_client():
    """Test TextractClient functionality with mocked AWS services"""
    print("Testing TextractClient...")
    # Test successful text extraction
    print("\n1. Testing successful text extraction...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        # Mock Textract response
        mock_textract = Mock()
        mock_s3 = Mock()
        mock_boto3.side_effect = lambda service: {
            "textract": mock_textract,
            "s3": mock_s3,
        }[service]
        # Mock PDFValidator
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": True}
        mock_validator.get_detailed_file_info.return_value = {"size_mb": 1, "content_type": "application/pdf"}
        mock_validator_class.return_value = mock_validator
        # Mock successful Textract response
        mock_textract.detect_document_text.return_value = {
            "Blocks": [
                {"BlockType": "LINE", "Text": "John Doe"},
                {"BlockType": "LINE", "Text": "Software Engineer"},
                {"BlockType": "LINE", "Text": "Python, AWS, Docker"},
                {"BlockType": "WORD", "Text": "ignored"},  # Should be ignored
            ]
        }
        # Mock S3 head_object (file exists)
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        client = TextractClient()
        result = client.extract_text_from_s3_pdf("test-bucket", "resume.pdf")
        assert result["success"] == True
        assert "John Doe" in result["text"]
        assert "Software Engineer" in result["text"]
        assert "Python, AWS, Docker" in result["text"]
        print("✓ Successful text extraction works")

    # Test unsupported file format
    print("\n2. Testing unsupported file format...")
    with patch("textract_client.boto3.client"), patch("textract_client.PDFValidator") as mock_validator_class:
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": False, "error": "Unsupported file format"}
        mock_validator_class.return_value = mock_validator
        client = TextractClient()
        result = client.extract_text_from_s3_pdf("test-bucket", "resume.docx")
        assert result["success"] == False
        assert "Unsupported file format" in result["error"]
        print("✓ Unsupported file format detection works")

    # Test file not found
    print("\n3. Testing file not found...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        # Mock 404 error for s3.head_object
        error_response = {"Error": {"Code": "404"}}
        mock_s3.head_object.side_effect = ClientError(error_response, "HeadObject")
        # Mock PDFValidator (should not be called in this case)
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        client = TextractClient()
        result = client.extract_text_from_s3_pdf("test-bucket", "nonexistent.pdf")
        assert result["success"] == False
        assert "File not found" in result["error"]
        print("✓ File not found handling works")

    # Test corrupted/password-protected PDF
    print("\n4. Testing corrupted PDF...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        mock_textract = Mock()
        mock_s3 = Mock()
        mock_boto3.side_effect = lambda service: {
            "textract": mock_textract,
            "s3": mock_s3,
        }[service]
        # Mock S3 success but Textract failure
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        error_response = {"Error": {"Code": "InvalidS3ObjectException"}}
        mock_textract.detect_document_text.side_effect = ClientError(
            error_response, "DetectDocumentText"
        )
        # Mock PDFValidator
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": True}
        mock_validator_class.return_value = mock_validator
        client = TextractClient()
        result = client.extract_text_from_s3_pdf("test-bucket", "corrupted.pdf")
        assert result["success"] == False
        assert "corrupted or password-protected" in result["error"]
        print("✓ Corrupted PDF handling works")

    # Test empty PDF (no text extracted)
    print("\n5. Testing empty PDF...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        mock_textract = Mock()
        mock_s3 = Mock()
        mock_boto3.side_effect = lambda service: {
            "textract": mock_textract,
            "s3": mock_s3,
        }[service]
        # Mock empty Textract response
        mock_textract.detect_document_text.return_value = {"Blocks": []}
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        # Mock PDFValidator
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": True}
        mock_validator_class.return_value = mock_validator
        client = TextractClient()
        result = client.extract_text_from_s3_pdf("test-bucket", "empty.pdf")
        assert result["success"] == False
        assert "No text could be extracted" in result["error"]
        print("✓ Empty PDF handling works")

@patch("textract_client.boto3.client")
def test_s3_handler(mock_boto3):
    """Test S3Handler functionality"""
    mock_s3 = Mock()
    mock_boto3.return_value = mock_s3
    print("\n\nTesting S3Handler...")
    # Test valid S3 event processing
    print("\n1. Testing valid S3 event processing...")
    s3_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "resumes/user123/resume.pdf"},
                }
            }
        ]
    }
    handler = S3Handler()
    result = handler.handle_s3_upload_event(s3_event)
    assert result["success"] == True
    assert result["bucket_name"] == "test-bucket"
    assert result["s3_key"] == "resumes/user123/resume.pdf"
    print("✓ Valid S3 event processing works")
    # Test invalid S3 event
    print("\n2. Testing invalid S3 event...")
    invalid_event = {"invalid": "event"}
    result = handler.handle_s3_upload_event(invalid_event)
    assert result["success"] == False
    assert "no Records found" in result["error"]
    print("✓ Invalid S3 event handling works")

def test_lambda_handler():
    """Test main Lambda handler"""
    print("\n\nTesting Lambda Handler...")
    # Test direct invocation
    print("\n1. Testing direct invocation...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        mock_textract = Mock()
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_boto3.side_effect = lambda service: {
            "textract": mock_textract,
            "s3": mock_s3,
            "bedrock-runtime": mock_bedrock,
        }[service]
        # Mock successful responses
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        mock_textract.detect_document_text.return_value = {
            "Blocks": [{"BlockType": "LINE", "Text": "Test Resume Content"}]
        }
        # Mock PDFValidator
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": True}
        mock_validator_class.return_value = mock_validator
        event = {"bucket_name": "test-bucket", "s3_key": "test-resume.pdf"}
        result = lambda_handler(event, {})
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["success"] == True
        assert "Test Resume Content" in body["extracted_text"]
        print("✓ Direct invocation works")

    # Test S3 upload event
    print("\n2. Testing S3 upload event...")
    with patch("textract_client.boto3.client") as mock_boto3, patch("textract_client.PDFValidator") as mock_validator_class:
        mock_textract = Mock()
        mock_s3 = Mock()
        mock_bedrock = Mock()
        mock_boto3.side_effect = lambda service: {
            "textract": mock_textract,
            "s3": mock_s3,
            "bedrock-runtime": mock_bedrock,
        }[service]
        # Mock successful responses
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        mock_textract.detect_document_text.return_value = {
            "Blocks": [{"BlockType": "LINE", "Text": "Resume from S3 Upload"}]
        }
        # Mock PDFValidator
        mock_validator = Mock()
        mock_validator.validate_pdf_structure.return_value = {"valid": True}
        mock_validator_class.return_value = mock_validator
        s3_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "upload-bucket"},
                        "object": {"key": "uploads/resume.pdf"},
                    }
                }
            ]
        }
        result = lambda_handler(s3_event, {})
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["success"] == True
        assert "Resume from S3 Upload" in body["extracted_text"]
        print("✓ S3 upload event works")

    # Test invalid event
    print("\n3. Testing invalid event...")
    invalid_event = {"invalid": "format"}
    result = lambda_handler(invalid_event, {})
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert body["success"] == False
    assert "Invalid event format" in body["error"]
    print("✓ Invalid event handling works")

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("ATS Buddy S3 and Textract Integration Tests")
    print("=" * 60)
    try:
        test_textract_client()
        test_s3_handler()
        test_lambda_handler()
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("S3 and Textract integration is working correctly")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
