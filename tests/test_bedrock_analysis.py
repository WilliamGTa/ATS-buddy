"""
Test suite for Bedrock AI analysis functionality
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.bedrock_client import BedrockClient

# Sample test data
SAMPLE_RESUME_TEXT = """
John Doe
Software Engineer

EXPERIENCE:
- 3 years Python development
- Built REST APIs using Flask
- Database experience with PostgreSQL
- Git version control

SKILLS:
- Python, JavaScript, SQL
- Flask, Django
- PostgreSQL, MySQL
- Git, Linux

EDUCATION:
Bachelor of Computer Science
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Software Engineer Position

Requirements:
- 5+ years Python experience
- AWS cloud experience required
- Docker containerization
- Kubernetes orchestration
- CI/CD pipeline experience
- Strong communication skills
- Leadership experience preferred

Technical Skills:
- Python, Java, Go
- AWS services (EC2, S3, Lambda)
- Docker, Kubernetes
- Jenkins, GitLab CI
- Microservices architecture
"""

SAMPLE_BEDROCK_RESPONSE = {
    "content": [
        {
            "text": json.dumps(
                {
                    "missing_keywords": [
                        "AWS",
                        "Docker",
                        "Kubernetes",
                        "CI/CD",
                        "Jenkins",
                    ],
                    "missing_skills": {
                        "technical": ["Docker", "Kubernetes", "AWS", "Jenkins"],
                        "soft": ["leadership", "communication"],
                    },
                    "suggestions": [
                        "Add AWS cloud experience to your technical skills section",
                        "Include Docker and Kubernetes experience in your projects",
                        "Highlight any CI/CD pipeline work you've done",
                    ],
                    "compatibility_score": 65,
                    "strengths": [
                        "Python experience",
                        "Database skills",
                        "API development",
                    ],
                    "areas_for_improvement": [
                        "Cloud experience",
                        "DevOps skills",
                        "Leadership experience",
                    ],
                }
            )
        }
    ]
}


class TestBedrockClient:

    def setup_method(self):
        """Setup test fixtures"""
        self.bedrock_client = BedrockClient()

    @patch("src.bedrock_client.boto3.client")
    def test_bedrock_client_initialization(self, mock_boto3):
        """Test Bedrock client initialization"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        client = BedrockClient()

        mock_boto3.assert_called_with("bedrock-runtime")
        assert client.model_id == "apac.amazon.nova-lite-v1:0"

    @patch("src.bedrock_client.BedrockClient._parse_analysis_response")
    @patch("src.bedrock_client.boto3.client")
    def test_successful_analysis(self, mock_boto3, mock_parse):
        """Test successful resume analysis"""
        # Setup mocks
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        # Create a proper mock response
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps(SAMPLE_BEDROCK_RESPONSE).encode()
        
        mock_response = MagicMock()
        mock_response.__getitem__.return_value = mock_response_body
        
        # Construct the expected nested structure
        expected_response = {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(SAMPLE_BEDROCK_RESPONSE)}]
                }
            }
        }
        mock_response_body.read.return_value = json.dumps(expected_response).encode()
        
        mock_bedrock.invoke_model.return_value = mock_response

        mock_parse.return_value = {
            "success": True,
            "data": {
                "missing_keywords": ["AWS", "Docker", "Kubernetes"],
                "missing_skills": {
                    "technical": ["Docker", "AWS"],
                    "soft": ["leadership"],
                },
                "suggestions": [
                    "Add AWS experience",
                    "Include Docker skills",
                    "Highlight leadership",
                ],
                "compatibility_score": 65,
                "strengths": ["Python experience"],
                "areas_for_improvement": ["Cloud experience"]
            },
        }

        client = BedrockClient()
        result = client.analyze_resume_vs_job_description(
            SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION
        )

        print(f"Result from analyze_resume_vs_job_description: {result}")
        assert result["success"] is True
        assert "analysis" in result
        assert len(result["analysis"]["suggestions"]) >= 3
        assert "missing_keywords" in result["analysis"]
        assert "compatibility_score" in result["analysis"]

    def test_empty_resume_text(self):
        """Test analysis with empty resume text"""
        result = self.bedrock_client.analyze_resume_vs_job_description(
            "", SAMPLE_JOB_DESCRIPTION
        )

        assert result["success"] is False
        assert "Resume text is empty" in result["error"]

    def test_empty_job_description(self):
        """Test analysis with empty job description"""
        result = self.bedrock_client.analyze_resume_vs_job_description(
            SAMPLE_RESUME_TEXT, ""
        )

        assert result["success"] is False
        assert "Job description is empty" in result["error"]

    @patch("src.bedrock_client.boto3.client")
    def test_bedrock_access_denied_error(self, mock_boto3):
        """Test handling of access denied error"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "AccessDeniedException", "Message": "Access denied"}
        }
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response, "InvokeModel"
        )

        client = BedrockClient()
        result = client.analyze_resume_vs_job_description(
            SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION
        )

        assert result["success"] is False
        assert "Access denied to Bedrock service" in result["error"]

    @patch("src.bedrock_client.boto3.client")
    def test_model_not_ready_error(self, mock_boto3):
        """Test handling of model not ready error"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "ModelNotReadyException", "Message": "Model not ready"}
        }
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response, "InvokeModel"
        )

        client = BedrockClient()
        result = client.analyze_resume_vs_job_description(
            SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION
        )

        assert result["success"] is False
        assert "AI model is not available" in result["error"]

    @patch("src.bedrock_client.boto3.client")
    def test_throttling_error(self, mock_boto3):
        """Test handling of throttling error"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "ThrottlingException", "Message": "Request throttled"}
        }
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response, "InvokeModel"
        )

        client = BedrockClient()
        result = client.analyze_resume_vs_job_description(
            SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION
        )

        assert result["success"] is False
        assert "Analysis service is busy" in result["error"]

    def test_create_analysis_prompt(self):
        """Test prompt creation for analysis"""
        prompt = self.bedrock_client._create_analysis_prompt(
            SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION
        )

        assert SAMPLE_RESUME_TEXT in prompt
        assert SAMPLE_JOB_DESCRIPTION in prompt
        assert "missing_keywords" in prompt
        assert "suggestions" in prompt
        assert "compatibility_score" in prompt
        assert "JSON format" in prompt

    def test_parse_valid_analysis_response(self):
        """Test parsing valid JSON analysis response"""
        valid_json = json.dumps(
            {
                "missing_keywords": ["AWS", "Docker"],
                "missing_skills": {"technical": ["Docker"], "soft": ["leadership"]},
                "suggestions": ["Add AWS", "Include Docker", "Show leadership"],
                "compatibility_score": 75,
            }
        )

        result = self.bedrock_client._parse_analysis_response(valid_json)

        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]["suggestions"]) >= 3
        assert result["data"]["compatibility_score"] == 75

    def test_parse_invalid_json_response(self):
        """Test parsing invalid JSON response"""
        invalid_json = "This is not valid JSON"

        result = self.bedrock_client._parse_analysis_response(invalid_json)

        assert result["success"] is False
        assert "No valid JSON found" in result["error"]

    def test_parse_incomplete_analysis_response(self):
        """Test parsing JSON with missing required fields"""
        incomplete_json = json.dumps(
            {
                "missing_keywords": ["AWS"],
                # Missing other required fields
            }
        )

        result = self.bedrock_client._parse_analysis_response(incomplete_json)

        assert result["success"] is False
        assert "Missing required field" in result["error"]

    def test_parse_response_with_extra_text(self):
        """Test parsing response with extra text around JSON"""
        response_with_extra = f"""
        Here is the analysis:
        
        {json.dumps({
            "missing_keywords": ["AWS"],
            "missing_skills": {"technical": ["AWS"], "soft": []},
            "suggestions": ["Add AWS", "Include cloud", "Show experience"],
            "compatibility_score": 60
        })}
        
        Hope this helps!
        """

        result = self.bedrock_client._parse_analysis_response(response_with_extra)

        assert result["success"] is True
        assert result["data"]["compatibility_score"] == 60

    def test_parse_response_ensures_minimum_suggestions(self):
        """Test that parser ensures at least 3 suggestions"""
        json_with_few_suggestions = json.dumps(
            {
                "missing_keywords": ["AWS"],
                "missing_skills": {"technical": ["AWS"], "soft": []},
                "suggestions": ["Add AWS"],  # Only 1 suggestion
                "compatibility_score": 60,
            }
        )

        result = self.bedrock_client._parse_analysis_response(json_with_few_suggestions)

        assert result["success"] is True
        assert len(result["data"]["suggestions"]) >= 3

    def test_parse_response_validates_score_range(self):
        """Test that compatibility score is validated to 0-100 range"""
        json_with_invalid_score = json.dumps(
            {
                "missing_keywords": ["AWS"],
                "missing_skills": {"technical": ["AWS"], "soft": []},
                "suggestions": ["Add AWS", "Include cloud", "Show experience"],
                "compatibility_score": 150,  # Invalid score > 100
            }
        )

        result = self.bedrock_client._parse_analysis_response(json_with_invalid_score)

        assert result["success"] is True
        assert 0 <= result["data"]["compatibility_score"] <= 100

    @patch("src.bedrock_client.boto3.client")
    def test_bedrock_connection_test_success(self, mock_boto3):
        """Test successful Bedrock connection test"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        # Create a proper mock response 
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps({
            "output": {
                "message": {
                    "content": [{"text": "Connection successful"}]
                }
            }
        }).encode()
        
        mock_response = MagicMock()
        mock_response.__getitem__.return_value = mock_response_body
        
        mock_bedrock.invoke_model.return_value = mock_response

        client = BedrockClient()
        result = client.test_bedrock_connection()

        assert result["success"] is True
        assert "Bedrock connection successful" in result["message"]
        assert result["model_id"] == client.model_id

    @patch("src.bedrock_client.boto3.client")
    def test_bedrock_connection_test_failure(self, mock_boto3):
        """Test failed Bedrock connection test"""
        mock_bedrock = Mock()
        mock_boto3.return_value = mock_bedrock

        mock_bedrock.invoke_model.side_effect = Exception("Connection failed")

        client = BedrockClient()
        result = client.test_bedrock_connection()

        assert result["success"] is False
        assert "Bedrock connection failed" in result["error"]


def test_integration_with_sample_data():
    """Integration test with sample resume and job description"""
    # This test would require actual AWS credentials and Bedrock access
    # For now, it's a placeholder for manual testing
    pass


if __name__ == "__main__":
    # Run basic tests
    print("Running Bedrock client tests...")

    # Test client initialization
    client = BedrockClient()
    print(f"✓ Client initialized with model: {client.model_id}")

    # Test prompt creation
    prompt = client._create_analysis_prompt(SAMPLE_RESUME_TEXT, SAMPLE_JOB_DESCRIPTION)
    print(f"✓ Prompt created (length: {len(prompt)} chars)")

    # Test JSON parsing
    sample_json = json.dumps(
        {
            "missing_keywords": ["AWS", "Docker"],
            "missing_skills": {"technical": ["Docker"], "soft": ["leadership"]},
            "suggestions": ["Add AWS", "Include Docker", "Show leadership"],
            "compatibility_score": 75,
        }
    )

    result = client._parse_analysis_response(sample_json)
    if result["success"]:
        print("✓ JSON parsing works correctly")
        print(f"  - Found {len(result['data']['missing_keywords'])} missing keywords")
        print(f"  - Generated {len(result['data']['suggestions'])} suggestions")
        print(f"  - Compatibility score: {result['data']['compatibility_score']}")
    else:
        print(f"✗ JSON parsing failed: {result['error']}")

    print("\nBedrock client tests completed!")