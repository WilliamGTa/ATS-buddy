#!/usr/bin/env python3
"""
Unit tests for API Gateway integration functionality
"""

import unittest
import json
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from handler import (
    is_api_gateway_request, 
    handle_api_gateway_request,
    parse_multipart_form_data,
    create_cors_response
)

class TestAPIGatewayIntegration(unittest.TestCase):
    
    def test_api_gateway_detection_v1(self):
        """Test API Gateway v1 format detection"""
        event = {
            "httpMethod": "POST",
            "path": "/analyze",
            "headers": {"content-type": "application/json"}
        }
        self.assertTrue(is_api_gateway_request(event))
    
    def test_api_gateway_detection_v2(self):
        """Test API Gateway v2 format detection"""
        event = {
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/analyze"
                }
            }
        }
        self.assertTrue(is_api_gateway_request(event))
    
    def test_lambda_event_detection(self):
        """Test that regular Lambda events are not detected as API Gateway"""
        event = {
            "bucket_name": "test-bucket",
            "s3_key": "test.pdf",
            "job_description": "Test job"
        }
        self.assertFalse(is_api_gateway_request(event))
    
    def test_cors_response_format(self):
        """Test CORS response format"""
        response = create_cors_response(200, {"message": "test"})
        
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Access-Control-Allow-Origin", response["headers"])
        self.assertIn("Access-Control-Allow-Methods", response["headers"])
        self.assertIn("Access-Control-Allow-Headers", response["headers"])
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], "*")
        
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "test")
    
    def test_multipart_form_parsing_success(self):
        """Test successful multipart form data parsing"""
        event = {
            "headers": {
                "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
            },
            "body": """------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="resume"; filename="test.pdf"\r
Content-Type: application/pdf\r
\r
%PDF-1.4 fake pdf content for testing with enough content to pass validation\r
------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="jobDescription"\r
\r
Software Engineer position requiring Python, AWS, and machine learning experience. Must have 3+ years of experience in backend development and strong problem-solving skills.\r
------WebKitFormBoundary7MA4YWxkTrZu0gW--\r
""",
            "isBase64Encoded": False
        }
        
        result = parse_multipart_form_data(event)
        
        self.assertTrue(result["success"])
        self.assertIn("pdf_content", result)
        self.assertIn("job_description", result)
        self.assertGreater(len(result["job_description"]), 50)
    
    def test_multipart_form_parsing_missing_pdf(self):
        """Test multipart form parsing with missing PDF"""
        event = {
            "headers": {
                "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
            },
            "body": """------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="jobDescription"\r
\r
Software Engineer position requiring Python, AWS, and machine learning experience.\r
------WebKitFormBoundary7MA4YWxkTrZu0gW--\r
""",
            "isBase64Encoded": False
        }
        
        result = parse_multipart_form_data(event)
        
        self.assertFalse(result["success"])
        self.assertIn("PDF file is required", result["error"])
    
    def test_multipart_form_parsing_short_job_description(self):
        """Test multipart form parsing with too short job description"""
        event = {
            "headers": {
                "content-type": "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"
            },
            "body": """------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="resume"; filename="test.pdf"\r
Content-Type: application/pdf\r
\r
%PDF-1.4 fake pdf content\r
------WebKitFormBoundary7MA4YWxkTrZu0gW\r
Content-Disposition: form-data; name="jobDescription"\r
\r
Short job\r
------WebKitFormBoundary7MA4YWxkTrZu0gW--\r
""",
            "isBase64Encoded": False
        }
        
        result = parse_multipart_form_data(event)
        
        self.assertFalse(result["success"])
        self.assertIn("must be at least 50 characters", result["error"])
    
    def test_multipart_form_parsing_invalid_content_type(self):
        """Test multipart form parsing with invalid content type"""
        event = {
            "headers": {
                "content-type": "application/json"
            },
            "body": '{"test": "data"}',
            "isBase64Encoded": False
        }
        
        result = parse_multipart_form_data(event)
        
        self.assertFalse(result["success"])
        self.assertIn("Content-Type must be multipart/form-data", result["error"])

if __name__ == "__main__":
    unittest.main()