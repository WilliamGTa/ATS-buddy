"""
ATS Buddy - AI-powered resume optimization tool

This package contains the core components for analyzing resumes against job descriptions
and generating improvement suggestions using AWS services.
"""

__version__ = "1.0.0"
__author__ = "ATS Buddy Team"

# Main components
from .handler import lambda_handler
from .textract_client import TextractClient
from .bedrock_client import BedrockClient
from .report_generator import ReportGenerator
from .s3_handler import S3Handler

__all__ = [
    "lambda_handler",
    "TextractClient",
    "BedrockClient",
    "ReportGenerator",
    "S3Handler",
]
