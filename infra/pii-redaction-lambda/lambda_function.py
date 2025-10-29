"""
S3 Object Lambda function for PII redaction using Amazon Comprehend
"""

import json
import boto3
import urllib.request
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
s3 = boto3.client('s3')
comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    """
    S3 Object Lambda handler for PII redaction
    """
    logger.info(f"Received S3 Object Lambda event")
    
    try:
        # Get the object context from the input
        object_context = event["getObjectContext"]
        request_route = object_context["outputRoute"]
        request_token = object_context["outputToken"]
        s3_url = object_context["inputS3Url"]
        
        logger.info(f"Processing request for: {s3_url}")
        
        # Get the original object from S3 using the presigned URL
        with urllib.request.urlopen(s3_url) as response:
            original_object = response.read()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        logger.info(f"Retrieved object, size: {len(original_object)} bytes, type: {content_type}")
        
        # For PDF files, pass through unchanged
        # Textract will extract text and we can apply PII redaction at the application level
        if content_type == 'application/pdf' or s3_url.lower().endswith('.pdf'):
            logger.info("PDF file - passing through unchanged for Textract processing")
            transformed_object = original_object
        
        elif content_type.startswith('text/') or 'text' in content_type.lower():
            # For text files, apply PII redaction
            try:
                text_content = original_object.decode('utf-8')
                logger.info(f"Processing text content: {len(text_content)} characters")
                
                redacted_text = redact_pii_from_text(text_content)
                transformed_object = redacted_text.encode('utf-8')
                
                logger.info(f"Applied PII redaction: {len(text_content)} -> {len(redacted_text)} chars")
            except UnicodeDecodeError:
                logger.warning("Could not decode as UTF-8, passing through unchanged")
                transformed_object = original_object
        
        else:
            # For other file types, pass through unchanged
            logger.info(f"Non-text content type {content_type}, passing through unchanged")
            transformed_object = original_object
        
        # Write the transformed object back to S3 Object Lambda
        s3.write_get_object_response(
            Body=transformed_object,
            RequestRoute=request_route,
            RequestToken=request_token,
            ContentType=content_type
        )
        
        logger.info("Successfully processed S3 Object Lambda request")
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error processing S3 Object Lambda request: {str(e)}", exc_info=True)
        
        # Return error response
        try:
            s3.write_get_object_response(
                RequestRoute=request_route,
                RequestToken=request_token,
                StatusCode=500,
                ErrorCode='InternalError',
                ErrorMessage=str(e)
            )
        except Exception as write_error:
            logger.error(f"Failed to write error response: {write_error}")
            
        raise e

def redact_pii_from_text(text):
    """
    Redact PII from text using Amazon Comprehend
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with PII redacted
    """
    try:
        # Detect PII entities using Comprehend
        response = comprehend.detect_pii_entities(
            Text=text,
            LanguageCode='en'
        )
        
        entities = response.get('Entities', [])
        
        if not entities:
            logger.info("No PII entities detected")
            return text
        
        # Sort entities by begin offset in descending order to avoid offset shifts
        entities.sort(key=lambda x: x['BeginOffset'], reverse=True)
        
        redacted_text = text
        redaction_count = 0
        
        for entity in entities:
            entity_type = entity['Type']
            confidence = entity['Score']
            begin_offset = entity['BeginOffset']
            end_offset = entity['EndOffset']
            
            # Only redact high-confidence PII
            if confidence >= 0.5:
                # Replace PII with asterisks
                pii_length = end_offset - begin_offset
                redaction = '*' * min(pii_length, 8)  # Limit asterisks to 8 characters
                
                redacted_text = (
                    redacted_text[:begin_offset] + 
                    redaction + 
                    redacted_text[end_offset:]
                )
                
                redaction_count += 1
                logger.info(f"Redacted {entity_type} (confidence: {confidence:.2f})")
        
        logger.info(f"Redacted {redaction_count} PII entities")
        return redacted_text
        
    except ClientError as e:
        logger.error(f"Comprehend API error: {e}")
        # If Comprehend fails, return original text
        return text
    
    except Exception as e:
        logger.error(f"Error in PII redaction: {e}")
        # If redaction fails, return original text
        return text