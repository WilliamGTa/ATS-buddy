# ATS Buddy Lambda Handler
# Main entry point for the ATS Buddy serverless application

import json
import logging
import os
import base64
import uuid
from textract_client import TextractClient
from s3_handler import S3Handler
from bedrock_client import BedrockClient
from report_generator import ReportGenerator
from deduplication_service import DeduplicationService
from enhanced_resume_generator import EnhancedResumeGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_pii_redaction_to_text(text):
    """
    Apply PII redaction to extracted text using Amazon Comprehend
    
    Args:
        text (str): Extracted text from PDF
        
    Returns:
        dict: Contains 'success', 'text', and 'redacted' status
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Only apply redaction if text contains potential PII patterns
        if not text or len(text.strip()) < 10:
            return {"success": True, "text": text, "redacted": False}
        
        # Check if Comprehend is available
        try:
            comprehend = boto3.client('comprehend')
            
            # Detect PII entities
            response = comprehend.detect_pii_entities(
                Text=text[:5000],  # Limit to first 5000 chars for API limits
                LanguageCode='en'
            )
            
            entities = response.get('Entities', [])
            
            if not entities:
                logger.info("No PII entities detected in extracted text")
                return {"success": True, "text": text, "redacted": False}
            
            # Sort entities by begin offset in descending order
            entities.sort(key=lambda x: x['BeginOffset'], reverse=True)
            
            redacted_text = text
            redaction_count = 0
            
            for entity in entities:
                confidence = entity['Score']
                begin_offset = entity['BeginOffset']
                end_offset = entity['EndOffset']
                entity_type = entity['Type']
                
                # Only redact high-confidence PII
                if confidence >= 0.7:  # Higher threshold for text redaction
                    pii_length = end_offset - begin_offset
                    redaction = '*' * min(pii_length, 8)
                    
                    redacted_text = (
                        redacted_text[:begin_offset] + 
                        redaction + 
                        redacted_text[end_offset:]
                    )
                    
                    redaction_count += 1
                    logger.info(f"Redacted {entity_type} (confidence: {confidence:.2f})")
            
            if redaction_count > 0:
                logger.info(f"Applied PII redaction to extracted text: {redaction_count} entities redacted")
                return {"success": True, "text": redacted_text, "redacted": True}
            else:
                return {"success": True, "text": text, "redacted": False}
                
        except ClientError as e:
            logger.warning(f"Comprehend API error, using original text: {e}")
            return {"success": True, "text": text, "redacted": False}
            
    except Exception as e:
        logger.warning(f"PII redaction failed, using original text: {e}")
        return {"success": True, "text": text, "redacted": False}


def lambda_handler(event, context):
    """
    Main Lambda handler for ATS Buddy processing
    Orchestrates complete pipeline: S3 upload → Textract → Bedrock → report generation
    Also handles API Gateway requests for web UI integration
    """
    logger.info("ATS Buddy Lambda handler started")
    logger.info(f"Event received: {json.dumps(event, default=str)}")

    try:
        # Check if this is an API Gateway request
        if is_api_gateway_request(event):
            return handle_api_gateway_request(event, context)

        # Input validation for direct Lambda invocations
        validation_result = validate_input(event)
        if not validation_result["valid"]:
            return create_error_response(400, validation_result["error"])

        # Initialize all clients
        s3_handler = S3Handler()
        textract_client = TextractClient()
        bedrock_client = BedrockClient()
        report_generator = ReportGenerator()
        deduplication_service = DeduplicationService()

        # Route to appropriate handler based on event type
        event_type = validation_result["event_type"]

        if event_type == "complete_pipeline":
            # Complete pipeline: PDF → analysis → report
            return handle_complete_pipeline(
                event, s3_handler, textract_client, bedrock_client, report_generator, deduplication_service
            )
        elif event_type == "s3_upload":
            # S3 upload event (text extraction only)
            return handle_s3_upload(event, s3_handler, textract_client)
        elif event_type == "direct_extraction":
            # Direct invocation with S3 parameters (text extraction only)
            return handle_direct_invocation(event, textract_client)
        elif event_type == "analysis_only":
            # Analysis with pre-extracted text
            return handle_complete_analysis(event, bedrock_client, report_generator)
        else:
            return create_error_response(400, "Unsupported event type")

    except Exception as e:
        logger.error(f"Unexpected error in lambda handler: {e}")
        return create_error_response(500, "Internal server error during processing")


def validate_input(event):
    """
    Validate input event and determine processing type

    Args:
        event (dict): Lambda event

    Returns:
        dict: Validation result with event type
    """
    try:
        # Complete pipeline: PDF + job description → full analysis
        if "bucket_name" in event and "s3_key" in event and "job_description" in event:
            if not event.get("job_description", "").strip():
                return {"valid": False, "error": "Job description cannot be empty"}
            return {"valid": True, "event_type": "complete_pipeline"}

        # S3 upload event (automatic trigger)
        elif "Records" in event and event["Records"]:
            return {"valid": True, "event_type": "s3_upload"}

        # Direct extraction (PDF processing only)
        elif "bucket_name" in event and "s3_key" in event:
            return {"valid": True, "event_type": "direct_extraction"}

        # Analysis with pre-extracted text
        elif "resume_text" in event and "job_description" in event:
            if not event.get("resume_text", "").strip():
                return {"valid": False, "error": "Resume text cannot be empty"}
            if not event.get("job_description", "").strip():
                return {"valid": False, "error": "Job description cannot be empty"}
            return {"valid": True, "event_type": "analysis_only"}

        else:
            return {
                "valid": False,
                "error": "Invalid event format. Expected: complete pipeline (bucket_name + s3_key + job_description), S3 upload event, direct extraction (bucket_name + s3_key), or analysis only (resume_text + job_description)",
            }

    except Exception as e:
        logger.error(f"Error validating input: {e}")
        return {"valid": False, "error": "Invalid event structure"}


def create_error_response(status_code, error_message):
    """
    Create standardized error response

    Args:
        status_code (int): HTTP status code
        error_message (str): Error message

    Returns:
        dict: Lambda response format
    """
    return {
        "statusCode": status_code,
        "body": json.dumps({"success": False, "error": error_message}),
    }


def create_success_response(data):
    """
    Create standardized success response

    Args:
        data (dict): Response data

    Returns:
        dict: Lambda response format
    """
    return {"statusCode": 200, "body": json.dumps({"success": True, **data})}


def handle_complete_pipeline(
    event, s3_handler, textract_client, bedrock_client, report_generator, deduplication_service
):
    """
    Handle complete pipeline: S3 PDF → Textract → Bedrock → Report Generation
    This is the main orchestration function for the full ATS Buddy workflow
    """
    logger.info("Starting complete pipeline processing")

    try:
        # Extract parameters
        bucket_name = event["bucket_name"]
        s3_key = event["s3_key"]
        job_description = event["job_description"]
        reports_bucket = event.get(
            "reports_bucket", os.environ.get("REPORTS_BUCKET", bucket_name)
        )
        resume_filename = event.get("resume_filename", s3_key.split("/")[-1])
        job_title = event.get("job_title", "Position")

        logger.info(f"Processing complete pipeline for: s3://{bucket_name}/{s3_key}")

        # Step 1: Check for file deduplication
        logger.info("Step 1: Checking for file deduplication")
        dedup_result = deduplication_service.check_file_deduplication(
            bucket_name, s3_key, resume_filename
        )
        
        if dedup_result["is_duplicate"]:
            logger.info(f"File is a duplicate: {dedup_result['message']}")
            extracted_text = dedup_result["cached_data"]["extracted_text"]
            logger.info(f"Using cached text ({len(extracted_text)} characters)")
            
            # Skip to analysis with cached text
            processing_status = "deduplicated"
        else:
            logger.info(f"File is unique: {dedup_result['message']}")
            
            # Step 2: Extract text from PDF using Textract
            logger.info("Step 2: Extracting text from PDF")
            extraction_result = textract_client.extract_text_from_s3_pdf(
                bucket_name, s3_key
            )
            if not extraction_result["success"]:
                return create_error_response(
                    422, f"Text extraction failed: {extraction_result['error']}"
                )

            extracted_text = extraction_result["text"]
            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
            
            # Step 2.1: Apply PII redaction to extracted text
            logger.info("Step 2.1: Applying PII redaction to extracted text")
            pii_result = apply_pii_redaction_to_text(extracted_text)
            if pii_result["success"]:
                extracted_text = pii_result["text"]
                if pii_result["redacted"]:
                    logger.info("PII redaction applied to extracted text")
                else:
                    logger.info("No PII redaction needed for extracted text")
            
            # Store in cache for future deduplication
            if dedup_result["file_hash"]:
                deduplication_service.store_processed_file(
                    dedup_result["file_hash"], extracted_text, resume_filename
                )
            
            processing_status = "processed"

        # Step 3: AI analysis using Bedrock
        logger.info("Step 3: Performing AI analysis")
        analysis_result = bedrock_client.analyze_resume_vs_job_description(
            extracted_text, job_description
        )
        if not analysis_result["success"]:
            return create_error_response(
                422, f"AI analysis failed: {analysis_result['error']}"
            )

        analysis_data = analysis_result["analysis"]
        logger.info(
            f"Analysis completed - Compatibility Score: {analysis_data['compatibility_score']}%"
        )

        # Step 4: Generate and store reports
        logger.info("Step 4: Generating and storing reports")
        report_package = report_generator.create_complete_report_package(
            analysis_data, reports_bucket, resume_filename, job_title
        )

        if not report_package["success"]:
            return create_error_response(
                500, f"Report generation failed: {report_package['error']}"
            )

        logger.info(
            f"Pipeline completed successfully - Report ID: {report_package['report_id']}"
        )

        # Step 5: Return comprehensive results
        return create_success_response(
            {
                "pipeline_status": "completed",
                "processing_steps": {
                    "deduplication_check": "success",
                    "text_extraction": processing_status,
                    "ai_analysis": "success",
                    "report_generation": "success",
                },
                "deduplication": {
                    "status": processing_status,
                    "message": dedup_result.get("message", "File processed"),
                    "file_hash": dedup_result.get("file_hash", "unknown")[:8] + "..." if dedup_result.get("file_hash") else "unknown"
                },
                "input_summary": {
                    "resume_file": f"s3://{bucket_name}/{s3_key}",
                    "resume_filename": resume_filename,
                    "job_title": job_title,
                    "extracted_text_length": len(extracted_text),
                    "job_description_length": len(job_description),
                },
                "analysis_summary": {
                    "compatibility_score": analysis_data["compatibility_score"],
                    "missing_keywords_count": len(
                        analysis_data.get("missing_keywords", [])
                    ),
                    "suggestions_count": len(analysis_data.get("suggestions", [])),
                    "strengths_count": len(analysis_data.get("strengths", [])),
                },
                "reports": {
                    "report_id": report_package["report_id"],
                    "timestamp": report_package["timestamp"],
                    "markdown": {
                        "s3_key": report_package["reports"]["markdown"]["s3_key"],
                        "download_url": report_package["reports"]["markdown"][
                            "download_url"
                        ],
                        "expires_at": report_package["reports"]["markdown"][
                            "expires_at"
                        ],
                    },
                    "html": {
                        "s3_key": report_package["reports"]["html"]["s3_key"],
                        "download_url": report_package["reports"]["html"][
                            "download_url"
                        ],
                        "expires_at": report_package["reports"]["html"]["expires_at"],
                    },
                },
                "metadata": report_package["metadata"],
            }
        )

    except KeyError as e:
        logger.error(f"Missing required parameter in complete pipeline: {e}")
        return create_error_response(400, f"Missing required parameter: {e}")
    except Exception as e:
        logger.error(f"Error in complete pipeline: {e}")
        return create_error_response(500, "Failed to complete processing pipeline")

def is_running_in_lambda(context):
    """
    Check if we're running in actual Lambda environment vs local testing
    
    Args:
        context: Lambda context object
        
    Returns:
        bool: True if running in Lambda, False if local
    """
    # If no context provided, we're running locally
    if context is None:
        return False
    
    # Check for Lambda-specific context attributes
    lambda_indicators = [
        hasattr(context, 'aws_request_id'),
        hasattr(context, 'invoked_function_arn'),
        hasattr(context, 'log_group_name')
    ]
    
    return any(lambda_indicators)

def handle_s3_upload(event, s3_handler, textract_client):
    """
    Handle S3 upload event and extract text from uploaded PDF
    """
    logger.info("Processing S3 upload event")

    try:
        # Parse S3 event
        s3_result = s3_handler.handle_s3_upload_event(event)
        if not s3_result["success"]:
            return create_error_response(400, s3_result["error"])

        bucket_name = s3_result["bucket_name"]
        s3_key = s3_result["s3_key"]

        # Skip validation - let Textract handle it
        logger.info("Skipping PDF validation in S3 upload handler")

        # Extract text from PDF
        extraction_result = textract_client.extract_text_from_s3_pdf(
            bucket_name, s3_key
        )

        if extraction_result["success"]:
            extracted_text = extraction_result["text"]
            
            # Apply PII redaction to extracted text
            pii_result = apply_pii_redaction_to_text(extracted_text)
            if pii_result["success"]:
                extracted_text = pii_result["text"]
            
            logger.info(
                f"Successfully processed S3 upload: {len(extracted_text)} characters extracted"
            )
            return create_success_response(
                {
                    "processing_type": "s3_upload",
                    "bucket_name": bucket_name,
                    "s3_key": s3_key,
                    "extracted_text": extracted_text,
                    "text_length": len(extracted_text),
                    "pii_redacted": pii_result.get("redacted", False),
                    "next_steps": "Text extracted successfully. Use this text with a job description for analysis.",
                }
            )
        else:
            return create_error_response(
                422, f"Text extraction failed: {extraction_result['error']}"
            )

    except Exception as e:
        logger.error(f"Error in S3 upload handler: {e}")
        return create_error_response(500, "Failed to process S3 upload event")


def handle_direct_invocation(event, textract_client):
    """
    Handle direct Lambda invocation with bucket and key parameters
    """
    logger.info("Processing direct invocation")

    try:
        bucket_name = event["bucket_name"]
        s3_key = event["s3_key"]

        logger.info(f"Processing file: s3://{bucket_name}/{s3_key}")

        # Skip validation - let Textract handle it
        logger.info("Skipping PDF validation in direct invocation handler")

        # Extract text from PDF
        extraction_result = textract_client.extract_text_from_s3_pdf(
            bucket_name, s3_key
        )

        if extraction_result["success"]:
            extracted_text = extraction_result["text"]
            
            # Apply PII redaction to extracted text
            pii_result = apply_pii_redaction_to_text(extracted_text)
            if pii_result["success"]:
                extracted_text = pii_result["text"]
            
            logger.info(
                f"Successfully processed direct invocation: {len(extracted_text)} characters extracted"
            )
            return create_success_response(
                {
                    "processing_type": "direct_extraction",
                    "bucket_name": bucket_name,
                    "s3_key": s3_key,
                    "extracted_text": extracted_text,
                    "text_length": len(extracted_text),
                    "pii_redacted": pii_result.get("redacted", False),
                    "next_steps": "Text extracted successfully. Use this text with a job description for analysis.",
                }
            )
        else:
            return create_error_response(
                422, f"Text extraction failed: {extraction_result['error']}"
            )

    except KeyError as e:
        logger.error(f"Missing required parameter in direct invocation: {e}")
        return create_error_response(400, f"Missing required parameter: {e}")
    except Exception as e:
        logger.error(f"Error in direct invocation handler: {e}")
        return create_error_response(500, "Failed to process direct invocation")


def handle_complete_analysis(event, bedrock_client, report_generator):
    """
    Handle complete analysis pipeline: AI analysis + report generation
    """
    logger.info("Processing complete analysis request")

    try:
        # Extract parameters
        resume_text = event["resume_text"]
        job_description = event["job_description"]
        reports_bucket = event.get(
            "reports_bucket", os.environ.get("REPORTS_BUCKET", "ats-buddy-reports")
        )
        resume_filename = event.get("resume_filename", "resume.txt")
        job_title = event.get("job_title", "Position")

        logger.info(
            f"Analyzing resume ({len(resume_text)} chars) vs job description ({len(job_description)} chars)"
        )

        # Step 1: AI Analysis
        analysis_result = bedrock_client.analyze_resume_vs_job_description(
            resume_text, job_description
        )

        if not analysis_result["success"]:
            return create_error_response(
                422, f"AI analysis failed: {analysis_result['error']}"
            )

        analysis_data = analysis_result["analysis"]
        logger.info(
            f"Analysis completed - Compatibility Score: {analysis_data['compatibility_score']}%"
        )

        # Step 2: Check if we should attempt S3 operations
        # Only try S3 if we have a valid bucket name and it's not a placeholder
        should_generate_reports = (
            reports_bucket and 
            reports_bucket != "ats-buddy-reports" and
            not reports_bucket.startswith("local-")
        )

        if should_generate_reports:
            try:
                # Step 2a: Generate and store reports in S3
                report_package = report_generator.create_complete_report_package(
                    analysis_data, reports_bucket, resume_filename, job_title
                )

                if report_package["success"]:
                    logger.info(
                        f"Analysis pipeline completed successfully - Report ID: {report_package['report_id']}"
                    )

                    # Return complete results with S3 reports
                    return create_success_response(
                        {
                            "processing_type": "analysis_only",
                            "analysis_summary": {
                                "compatibility_score": analysis_data["compatibility_score"],
                                "missing_keywords_count": len(
                                    analysis_data.get("missing_keywords", [])
                                ),
                                "suggestions_count": len(analysis_data.get("suggestions", [])),
                                "strengths_count": len(analysis_data.get("strengths", [])),
                            },
                            "reports": {
                                "report_id": report_package["report_id"],
                                "timestamp": report_package["timestamp"],
                                "markdown": {
                                    "s3_key": report_package["reports"]["markdown"]["s3_key"],
                                    "download_url": report_package["reports"]["markdown"][
                                        "download_url"
                                    ],
                                    "expires_at": report_package["reports"]["markdown"][
                                        "expires_at"
                                    ],
                                },
                                "html": {
                                    "s3_key": report_package["reports"]["html"]["s3_key"],
                                    "download_url": report_package["reports"]["html"][
                                        "download_url"
                                    ],
                                    "expires_at": report_package["reports"]["html"]["expires_at"],
                                },
                            },
                            "metadata": report_package["metadata"],
                        }
                    )
                else:
                    # S3 failed but analysis succeeded - return analysis results without reports
                    logger.warning(f"S3 report generation failed: {report_package['error']}")
                    return create_success_response(
                        {
                            "processing_type": "analysis_only",
                            "analysis_summary": {
                                "compatibility_score": analysis_data["compatibility_score"],
                                "missing_keywords_count": len(
                                    analysis_data.get("missing_keywords", [])
                                ),
                                "suggestions_count": len(analysis_data.get("suggestions", [])),
                                "strengths_count": len(analysis_data.get("strengths", [])),
                            },
                            "reports": {
                                "report_id": f"local-{resume_filename}-{job_title}",
                                "timestamp": "local-execution",
                                "message": "Analysis completed successfully but reports were not saved to S3",
                                "error": report_package.get("error", "S3 operation failed")
                            },
                            "metadata": {
                                "execution_mode": "local_fallback",
                                "s3_available": False
                            },
                        }
                    )

            except Exception as s3_error:
                # S3 operation failed but analysis succeeded
                logger.warning(f"S3 operation failed, returning analysis results only: {s3_error}")
                return create_success_response(
                    {
                        "processing_type": "analysis_only",
                        "analysis_summary": {
                            "compatibility_score": analysis_data["compatibility_score"],
                            "missing_keywords_count": len(
                                analysis_data.get("missing_keywords", [])
                            ),
                            "suggestions_count": len(analysis_data.get("suggestions", [])),
                            "strengths_count": len(analysis_data.get("strengths", [])),
                        },
                        "reports": {
                            "report_id": f"local-{resume_filename}-{job_title}",
                            "timestamp": "local-execution",
                            "message": "Analysis completed successfully but reports were not saved to S3",
                            "error": str(s3_error)
                        },
                        "metadata": {
                            "execution_mode": "local_fallback",
                            "s3_available": False
                        },
                    }
                )
        else:
            # Local execution - return analysis results without S3
            logger.info("Local execution detected - returning analysis results without S3 storage")
            return create_success_response(
                {
                    "processing_type": "analysis_only",
                    "analysis_summary": {
                        "compatibility_score": analysis_data["compatibility_score"],
                        "missing_keywords_count": len(
                            analysis_data.get("missing_keywords", [])
                        ),
                        "suggestions_count": len(analysis_data.get("suggestions", [])),
                        "strengths_count": len(analysis_data.get("strengths", [])),
                    },
                    "reports": {
                        "report_id": f"local-{resume_filename}-{job_title}",
                        "timestamp": "local-execution",
                        "message": "Analysis completed successfully (local mode - no S3 storage)",
                    },
                    "metadata": {
                        "execution_mode": "local",
                        "s3_available": False
                    },
                }
            )

    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        return create_error_response(400, f"Missing required parameter: {e}")
    except Exception as e:
        logger.error(f"Error in complete analysis: {e}")
        return create_error_response(500, "Failed to complete analysis pipeline")


def is_api_gateway_request(event):
    """
    Check if the event is from API Gateway
    
    Args:
        event (dict): Lambda event
        
    Returns:
        bool: True if API Gateway request, False otherwise
    """
    return (
        "requestContext" in event and 
        "http" in event.get("requestContext", {}) and
        "method" in event.get("requestContext", {}).get("http", {})
    ) or (
        "httpMethod" in event and 
        "headers" in event
    )


def handle_api_gateway_request(event, context):
    """
    Handle API Gateway HTTP requests for web UI integration
    
    Args:
        event (dict): API Gateway event
        context: Lambda context
        
    Returns:
        dict: API Gateway response format
    """
    logger.info("Processing API Gateway request")
    
    try:
        # Extract HTTP method and path
        http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
        path = event.get("path") or event.get("requestContext", {}).get("http", {}).get("path", "")
        
        logger.info(f"API Gateway request: {http_method} {path}")
        
        # Handle CORS preflight requests
        if http_method == "OPTIONS":
            return create_cors_response(200, {"message": "CORS preflight"})
        
        # Route to appropriate API handler
        if http_method == "POST" and path == "/analyze":
            return handle_analyze_endpoint(event)
        elif http_method == "POST" and path == "/enhance":
            return handle_enhance_endpoint(event)
        else:
            return create_cors_response(404, {"error": "Endpoint not found"})
            
    except Exception as e:
        logger.error(f"Error handling API Gateway request: {e}")
        return create_cors_response(500, {"error": "Internal server error"})


def handle_analyze_endpoint(event):
    """
    Handle POST /analyze endpoint for web UI
    Accepts multipart form data with PDF file and job description
    
    Args:
        event (dict): API Gateway event
        
    Returns:
        dict: API Gateway response with analysis results
    """
    logger.info("Processing /analyze endpoint")
    
    try:
        # Parse multipart form data
        form_data = parse_multipart_form_data(event)
        if not form_data["success"]:
            return create_cors_response(400, {"error": form_data["error"]})
        
        pdf_content = form_data["pdf_content"]
        job_description = form_data["job_description"]
        original_filename = form_data["original_filename"]
        
        # Initialize clients
        s3_handler = S3Handler()
        textract_client = TextractClient()
        bedrock_client = BedrockClient()
        report_generator = ReportGenerator()
        deduplication_service = DeduplicationService()
        
        # Check for file deduplication BEFORE uploading to S3
        logger.info("Checking for file deduplication based on content hash")
        
        # Calculate hash of the uploaded content
        import hashlib
        content_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Check cache for existing hash
        cached_data = deduplication_service.dynamodb_client.get_resume_cache(content_hash)
        
        if cached_data:
            logger.info(f"File is a duplicate - using cached data")
            extracted_text = cached_data["extracted_text"]
            processing_status = "deduplicated"
            # Use existing S3 reference (don't upload duplicate)
            bucket_name = os.environ.get("RESUMES_BUCKET")
            s3_key = f"cached/{content_hash[:8]}/{original_filename}"  # Virtual S3 key for reference
        else:
            logger.info(f"File is unique - uploading and processing")
            
            # Upload PDF to S3 using content hash (prevents duplicates)
            bucket_name = os.environ.get("RESUMES_BUCKET")
            s3_key = f"web-uploads/{content_hash[:8]}/{original_filename}"  # Use hash prefix instead of random session ID
            
            upload_result = s3_handler.upload_file_content(
                bucket_name, s3_key, pdf_content, "application/pdf"
            )
            
            if not upload_result["success"]:
                return create_cors_response(500, {"error": f"Failed to upload PDF: {upload_result['error']}"})
            
            # Extract text from PDF
            logger.info("Extracting text from uploaded PDF")
            extraction_result = textract_client.extract_text_from_s3_pdf(bucket_name, s3_key)
            
            if not extraction_result["success"]:
                return create_cors_response(422, {"error": f"Text extraction failed: {extraction_result['error']}"})
            
            extracted_text = extraction_result["text"]
            
            # Apply PII redaction to extracted text
            logger.info("Applying PII redaction to extracted text")
            pii_result = apply_pii_redaction_to_text(extracted_text)
            if pii_result["success"]:
                extracted_text = pii_result["text"]
                if pii_result["redacted"]:
                    logger.info("PII redaction applied to extracted text")
            
            # Store in cache for future deduplication
            deduplication_service.store_processed_file(
                content_hash, extracted_text, original_filename
            )
            
            processing_status = "processed"
        
        # Perform AI analysis
        logger.info("Performing AI analysis")
        analysis_result = bedrock_client.analyze_resume_vs_job_description(
            extracted_text, job_description
        )
        
        if not analysis_result["success"]:
            return create_cors_response(422, {"error": f"AI analysis failed: {analysis_result['error']}"})
        
        analysis_data = analysis_result["analysis"]
        
        # Generate reports
        logger.info("Generating reports")
        reports_bucket = os.environ.get("REPORTS_BUCKET")
        report_package = report_generator.create_complete_report_package(
            analysis_data, reports_bucket, original_filename, "Web Analysis"
        )
        
        # Prepare response data
        response_data = {
            "sessionId": content_hash[:8],  # Use hash prefix as session ID
            "resumeFilename": original_filename,  # Include original filename
            "compatibilityScore": analysis_data["compatibility_score"],
            "missingKeywords": analysis_data.get("missing_keywords", []),
            "missingSkills": {
                "technical": analysis_data.get("missing_technical_skills", []),
                "soft": analysis_data.get("missing_soft_skills", [])
            },
            "suggestions": analysis_data.get("suggestions", []),
            "strengths": analysis_data.get("strengths", []),
            "deduplicationStatus": processing_status,  # For web UI compatibility
            "deduplication": {
                "status": processing_status,
                "message": "File processed with content-based deduplication",
                "fileHash": content_hash[:8] + "...",
                "originalFilename": original_filename  # Also include in deduplication info
            },
            "analysis": {
                "textLength": len(extracted_text),
                "jobDescriptionLength": len(job_description),
                "processingTime": "completed"
            },
            "enhancementAvailable": True,
            "originalResumeText": extracted_text  # Store for enhancement
        }
        
        # Add report URLs if available
        if report_package["success"]:
            response_data["reports"] = {
                "markdown": {
                    "downloadUrl": report_package["reports"]["markdown"]["download_url"],
                    "expiresAt": report_package["reports"]["markdown"]["expires_at"]
                },
                "html": {
                    "downloadUrl": report_package["reports"]["html"]["download_url"],
                    "expiresAt": report_package["reports"]["html"]["expires_at"]
                }
            }
        
        logger.info(f"Analysis completed successfully for hash {content_hash[:8]}")
        return create_cors_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        return create_cors_response(500, {"error": "Analysis processing failed"})


def handle_enhance_endpoint(event):
    """
    Handle POST /enhance endpoint for enhanced resume generation
    Accepts JSON data with original resume text, job description, and analysis data
    
    Args:
        event (dict): API Gateway event
        
    Returns:
        dict: API Gateway response with enhanced resume
    """
    logger.info("Processing /enhance endpoint")
    
    try:
        # Parse JSON body
        body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body).decode('utf-8')
        
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            return create_cors_response(400, {"error": "Invalid JSON in request body"})
        
        # Extract required fields
        original_resume_text = request_data.get("originalResumeText", "")
        job_description = request_data.get("jobDescription", "")
        analysis_data = request_data.get("analysisData")
        
        # Validate required fields
        if not original_resume_text.strip():
            return create_cors_response(400, {"error": "Original resume text is required"})
        
        if not job_description.strip():
            return create_cors_response(400, {"error": "Job description is required"})
        
        # Initialize enhanced resume generator
        enhanced_generator = EnhancedResumeGenerator()
        
        # Generate enhanced resume
        logger.info("Generating enhanced resume")
        enhancement_result = enhanced_generator.generate_enhanced_resume(
            original_resume_text, job_description, analysis_data
        )
        
        if not enhancement_result["success"]:
            return create_cors_response(422, {"error": f"Enhancement failed: {enhancement_result['error']}"})
        
        # Prepare response
        response_data = {
            "success": True,
            "enhancedResume": enhancement_result["enhanced_resume"],
            "originalLength": enhancement_result["original_length"],
            "enhancedLength": enhancement_result["enhanced_length"],
            "keywordsAdded": enhancement_result["keywords_added"],
            "improvementsMade": enhancement_result["improvements_made"]
        }
        
        logger.info("Enhanced resume generated successfully")
        return create_cors_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Error in enhance endpoint: {e}")
        return create_cors_response(500, {"error": "Enhancement processing failed"})


def parse_multipart_form_data(event):
    """
    Parse multipart form data from API Gateway event
    
    Args:
        event (dict): API Gateway event
        
    Returns:
        dict: Parsed form data with pdf_content and job_description
    """
    try:
        # Get content type header
        headers = event.get("headers", {})
        content_type = headers.get("content-type") or headers.get("Content-Type", "")
        
        if not content_type.startswith("multipart/form-data"):
            return {"success": False, "error": "Content-Type must be multipart/form-data"}
        
        # Get body content
        body = event.get("body", "")
        is_base64 = event.get("isBase64Encoded", False)
        
        if is_base64:
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8')
        
        # Extract boundary from content type
        boundary = None
        for part in content_type.split(";"):
            part = part.strip()
            if part.startswith("boundary="):
                boundary = part.split("=", 1)[1].strip('"')
                break
        
        if not boundary:
            return {"success": False, "error": "No boundary found in Content-Type header"}
        
        # Parse multipart data
        boundary_bytes = f"--{boundary}".encode()
        parts = body.split(boundary_bytes)
        
        pdf_content = None
        job_description = None
        original_filename = "unknown.pdf"  # Default fallback
        
        for part in parts:
            if not part.strip() or part.strip() == b"--":
                continue
                
            # Split headers and content
            if b"\r\n\r\n" in part:
                headers_section, content = part.split(b"\r\n\r\n", 1)
            elif b"\n\n" in part:
                headers_section, content = part.split(b"\n\n", 1)
            else:
                continue
            
            headers_text = headers_section.decode('utf-8', errors='ignore')
            
            # Parse Content-Disposition header
            if 'name="resume"' in headers_text or 'name="pdf"' in headers_text:
                pdf_content = content.rstrip(b"\r\n--")
                
                # Extract filename from Content-Disposition header
                import re
                filename_match = re.search(r'filename="([^"]+)"', headers_text)
                if filename_match:
                    original_filename = filename_match.group(1)
                    
            elif 'name="jobDescription"' in headers_text or 'name="job_description"' in headers_text:
                job_description = content.rstrip(b"\r\n--").decode('utf-8', errors='ignore').strip()
        
        # Validate required fields
        if not pdf_content:
            return {"success": False, "error": "PDF file is required"}
        
        if not job_description:
            return {"success": False, "error": "Job description is required"}
        
        if len(job_description.strip()) < 50:
            return {"success": False, "error": "Job description must be at least 50 characters"}
        
        return {
            "success": True,
            "pdf_content": pdf_content,
            "job_description": job_description,
            "original_filename": original_filename
        }
        
    except Exception as e:
        logger.error(f"Error parsing multipart form data: {e}")
        return {"success": False, "error": "Failed to parse form data"}


def create_cors_response(status_code, data):
    """
    Create API Gateway response with CORS headers
    
    Args:
        status_code (int): HTTP status code
        data (dict): Response data
        
    Returns:
        dict: API Gateway response format with CORS headers
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With, X-Amz-Date, X-Api-Key, X-Amz-Security-Token",
            "Access-Control-Allow-Credentials": "false",
            "Access-Control-Max-Age": "86400"
        },
        "body": json.dumps(data)
    }