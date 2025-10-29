"""
Bedrock client for AI-powered resume analysis against job descriptions
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class BedrockClient:
    def __init__(self):
        """Initialize Bedrock client"""
        self.bedrock = boto3.client("bedrock-runtime")
        # Using Amazon Nova Lite inference profile
        self.model_id = "apac.amazon.nova-lite-v1:0"

    def analyze_resume_vs_job_description(self, resume_text, job_description):
        """
        Analyze resume against job description using Bedrock AI

        Args:
            resume_text (str): Extracted text from resume PDF
            job_description (str): Job description text

        Returns:
            dict: Contains 'success' boolean and either analysis results or 'error' message
        """
        try:
            # Validate inputs
            if not resume_text or not resume_text.strip():
                return {"success": False, "error": "Resume text is empty or invalid"}

            if not job_description or not job_description.strip():
                return {
                    "success": False,
                    "error": "Job description is empty or invalid",
                }

            # Create structured prompt for analysis
            prompt = self._create_analysis_prompt(resume_text, job_description)

            # Prepare request body for Nova Pro
            request_body = {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "max_new_tokens": 2000,
                    "temperature": 0.1,
                    "top_p": 0.9,
                },
            }

            logger.info("Sending analysis request to Bedrock")

            # Call Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract content from Nova Pro response
            if "output" in response_body and "message" in response_body["output"]:
                message = response_body["output"]["message"]
                if "content" in message and len(message["content"]) > 0:
                    analysis_text = message["content"][0]["text"]

                    # Parse the JSON analysis from the response
                    analysis_result = self._parse_analysis_response(analysis_text)

                    if analysis_result["success"]:
                        logger.info("Successfully completed resume analysis")
                        return {"success": True, "analysis": analysis_result["data"]}
                    else:
                        return analysis_result
                else:
                    return {
                        "success": False,
                        "error": "Invalid response format from AI model",
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid response format from AI model",
                }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "AccessDeniedException":
                return {
                    "success": False,
                    "error": "Access denied to Bedrock service. Check IAM permissions.",
                }
            elif error_code == "ValidationException":
                return {
                    "success": False,
                    "error": "Invalid request parameters for AI analysis.",
                }
            elif error_code == "ModelNotReadyException":
                return {
                    "success": False,
                    "error": "AI model is not available. Please try again later.",
                }
            elif error_code == "ThrottlingException":
                return {
                    "success": False,
                    "error": "Analysis service is busy. Please try again later.",
                }
            else:
                logger.error(f"Bedrock ClientError: {error_code} - {e}")
                return {
                    "success": False,
                    "error": "Analysis service unavailable due to service error.",
                }

        except BotoCoreError as e:
            logger.error(f"Bedrock BotoCoreError: {e}")
            return {
                "success": False,
                "error": "Analysis service unavailable due to connection error.",
            }

        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}")
            return {
                "success": False,
                "error": "Analysis failed due to unexpected error.",
            }

    def _create_analysis_prompt(self, resume_text, job_description):
        """
        Create structured prompt for resume analysis

        Args:
            resume_text (str): Resume content
            job_description (str): Job description content

        Returns:
            str: Formatted prompt for AI analysis
        """
        prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer. Compare the provided resume against the job description and identify gaps and improvement opportunities.

Resume Text:
{resume_text}

Job Description:
{job_description}

Please analyze the resume against the job description and return your analysis in the following JSON format:

{{
  "missing_keywords": ["keyword1", "keyword2", "keyword3"],
  "missing_skills": {{
    "technical": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"]
  }},
  "suggestions": [
    "Specific actionable suggestion 1",
    "Specific actionable suggestion 2", 
    "Specific actionable suggestion 3"
  ],
  "compatibility_score": 75,
  "strengths": ["strength1", "strength2"],
  "areas_for_improvement": ["area1", "area2"]
}}

Guidelines:
- Focus on keywords and skills explicitly mentioned in the job description
- Provide at least 3 actionable suggestions for improvement
- Score compatibility from 0-100 based on keyword/skill alignment
- Be specific and practical in suggestions
- Consider both technical skills and soft skills
- Return ONLY the JSON response, no additional text"""

        return prompt

    def _parse_analysis_response(self, response_text):
        """
        Parse AI analysis response and extract structured data

        Args:
            response_text (str): Raw response from AI model

        Returns:
            dict: Parsed analysis data or error information
        """
        try:
            # Clean the response text to extract JSON
            response_text = response_text.strip()

            # Find JSON content (handle cases where model adds extra text)
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return {"success": False, "error": "No valid JSON found in AI response"}

            json_text = response_text[start_idx:end_idx]
            analysis_data = json.loads(json_text)

            # Validate required fields
            required_fields = [
                "missing_keywords",
                "missing_skills",
                "suggestions",
                "compatibility_score",
            ]
            for field in required_fields:
                if field not in analysis_data:
                    return {
                        "success": False,
                        "error": f"Missing required field in analysis: {field}",
                    }

            # Validate data types and content
            if not isinstance(analysis_data["missing_keywords"], list):
                analysis_data["missing_keywords"] = []

            if not isinstance(analysis_data["missing_skills"], dict):
                analysis_data["missing_skills"] = {"technical": [], "soft": []}

            if not isinstance(analysis_data["suggestions"], list):
                analysis_data["suggestions"] = []

            # Ensure we have at least 3 suggestions as per requirements
            if len(analysis_data["suggestions"]) < 3:
                analysis_data["suggestions"].extend(
                    [
                        "Review job description keywords and incorporate relevant ones into your resume",
                        "Quantify your achievements with specific metrics and numbers",
                        "Tailor your skills section to match the job requirements",
                    ]
                )
                analysis_data["suggestions"] = analysis_data["suggestions"][:3]

            # Validate compatibility score
            try:
                score = float(analysis_data["compatibility_score"])
                analysis_data["compatibility_score"] = max(0, min(100, score))
            except (ValueError, TypeError):
                analysis_data["compatibility_score"] = 50  # Default score

            # Add default values for optional fields
            if "strengths" not in analysis_data:
                analysis_data["strengths"] = []
            if "areas_for_improvement" not in analysis_data:
                analysis_data["areas_for_improvement"] = []

            return {"success": True, "data": analysis_data}

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {"success": False, "error": "Invalid JSON format in AI response"}
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return {"success": False, "error": "Failed to parse AI analysis response"}

    def test_bedrock_connection(self):
        """
        Test Bedrock service connectivity and model availability

        Returns:
            dict: Contains 'success' boolean and connection status
        """
        try:
            # Simple test prompt
            test_prompt = "Hello, please respond with 'Connection successful'"

            request_body = {
                "messages": [{"role": "user", "content": [{"text": test_prompt}]}],
                "inferenceConfig": {
                    "max_new_tokens": 50,
                    "temperature": 0,
                    "top_p": 0.9,
                },
            }

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())

            if "output" in response_body and "message" in response_body["output"]:
                message = response_body["output"]["message"]
                if "content" in message and len(message["content"]) > 0:
                    return {
                        "success": True,
                        "message": "Bedrock connection successful",
                        "model_id": self.model_id,
                    }
                else:
                    return {
                        "success": False,
                        "error": "Invalid response from Bedrock model",
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid response from Bedrock model",
                }

        except Exception as e:
            logger.error(f"Bedrock connection test failed: {e}")
            return {"success": False, "error": f"Bedrock connection failed: {str(e)}"}
