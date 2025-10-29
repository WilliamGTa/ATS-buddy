"""
Simple test for report generation functionality (without AWS dependencies)
Tests report formatting and content generation
"""
import json
import uuid
import sys
from datetime import datetime, timezone
import pytest
from unittest.mock import Mock, patch

# Sample analysis data for tests
SAMPLE_ANALYSIS = {
    "missing_keywords": [
        "Python", "AWS", "Docker", "Kubernetes", "CI/CD", "microservices", "REST API", "PostgreSQL",
    ],
    "missing_skills": {
        "technical": [
            "Docker containerization",
            "Kubernetes orchestration",
            "AWS Lambda",
            "PostgreSQL",
        ],
        "soft": [
            "team leadership",
            "cross-functional collaboration",
            "agile methodology",
        ],
    },
    "suggestions": [
        "Add specific Python frameworks you've used (Django, Flask, FastAPI) to your technical skills section",
        "Include quantified achievements like 'Reduced deployment time by 40% using Docker containers'",
        "Mention your experience with cloud platforms, specifically AWS services like Lambda, S3, and RDS",
    ],
    "compatibility_score": 72,
    "strengths": [
        "Strong software development experience",
        "Database management skills",
        "Problem-solving abilities",
    ],
    "areas_for_improvement": [
        "Cloud platform experience needs more emphasis",
        "DevOps skills could be highlighted better",
    ],
}

# Mock the boto3 dependency for testing
class MockS3Client:
    def put_object(self, **kwargs):
        return {"ETag": '"mock-etag"'}
    def generate_presigned_url(self, ClientMethod, Params, ExpiresIn=None):
        bucket = Params["Bucket"]
        key = Params["Key"]
        return f"https://{bucket}.s3.amazonaws.com/{key}?mock-presigned-params"

# Pytest fixture to mock boto3 for all tests in this file
@pytest.fixture(autouse=True, scope="function")
def mock_boto3(mocker):
    # Use pytest-mock to patch boto3.client
    mock_client = mocker.patch("boto3.client")
    mock_s3 = Mock()
    mock_client.return_value = mock_s3
    mock_s3.put_object.return_value = {"ETag": '"mock-etag"'}
    mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test-key?mock-presigned-params"
    # Import the module under test after mocking
    from report_generator import ReportGenerator
    yield ReportGenerator()

class TestReportGenerator:
    """Test class for ReportGenerator functionality"""
    def test_report_content_generation(self, mock_boto3):
        """Test report content generation without AWS calls"""
        report_gen = mock_boto3
        # Test report generation
        report_result = report_gen.generate_report(
            SAMPLE_ANALYSIS,
            resume_filename="john_doe_resume.pdf",
            job_title="Senior Software Engineer",
        )
        # Assertions
        assert report_result["success"] is True
        assert "report_id" in report_result
        assert "markdown_content" in report_result
        assert "html_content" in report_result
        assert "metadata" in report_result

        # Check metadata
        metadata = report_result["metadata"]
        assert metadata["compatibility_score"] == 72
        assert metadata["missing_keywords_count"] == 8
        assert metadata["suggestions_count"] == 3

    def test_markdown_content_structure(self, mock_boto3):
        """Test Markdown report structure"""
        report_gen = mock_boto3
        report_result = report_gen.generate_report(SAMPLE_ANALYSIS)

        markdown_content = report_result["markdown_content"]

        # Check essential sections
        assert "# ATS Buddy - Resume Analysis Report" in markdown_content
        assert "## Compatibility Score" in markdown_content
        assert "## Key Findings" in markdown_content
        assert "## Your Strengths" in markdown_content
        assert "## Actionable Recommendations" in markdown_content
        assert "## Next Steps" in markdown_content

        # Check content
        assert "72%" in markdown_content  # Compatibility score
        assert "Python" in markdown_content  # Missing keyword
        assert "Docker" in markdown_content  # Missing skill

    def test_html_content_structure(self, mock_boto3):
        """Test HTML report structure"""
        report_gen = mock_boto3
        report_result = report_gen.generate_report(SAMPLE_ANALYSIS)

        html_content = report_result["html_content"]

        # Check HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "</html>" in html_content

        # Check content
        assert "72%" in html_content
        assert "Compatibility Score" in html_content
        assert "Missing Keywords" in html_content
        assert "Your Strengths" in html_content
        assert "Actionable Recommendations" in html_content

    def test_different_compatibility_scores(self, mock_boto3):
        """Test report generation with different compatibility scores"""
        test_cases = [
            (95, "Excellent match"),
            (75, "Good match"),
            (45, "Needs improvement"),
        ]

        for score, expected_text in test_cases:
            analysis = SAMPLE_ANALYSIS.copy()
            analysis["compatibility_score"] = score

            report_gen = mock_boto3
            report_result = report_gen.generate_report(analysis)
            markdown_content = report_result["markdown_content"]

            assert expected_text in markdown_content

    def test_empty_analysis_data(self, mock_boto3):
        """Test report generation with empty analysis data"""
        empty_analysis = {
            "missing_keywords": [],
            "missing_skills": {"technical": [], "soft": []},
            "suggestions": [],
            "compatibility_score": 0,
            "strengths": [],
            "areas_for_improvement": [],
        }

        report_gen = mock_boto3
        report_result = report_gen.generate_report(empty_analysis)

        assert report_result["success"] is True
        assert "0%" in report_result["markdown_content"]

    def test_report_with_filename_and_title(self, mock_boto3):
        """Test report generation with resume filename and job title"""
        report_gen = mock_boto3
        report_result = report_gen.generate_report(
            SAMPLE_ANALYSIS,
            resume_filename="test_resume.pdf",
            job_title="Software Developer"
        )

        markdown_content = report_result["markdown_content"]

        assert "test_resume.pdf" in markdown_content
        assert "Software Developer" in markdown_content

    def test_html_styling(self, mock_boto3):
        """Test HTML report styling elements"""
        report_gen = mock_boto3
        report_result = report_gen.generate_report(SAMPLE_ANALYSIS)
        html_content = report_result["html_content"]

        # Check CSS classes
        assert "class=\"container\"" in html_content
        assert "class=\"score-section\"" in html_content
        assert "class=\"metadata\"" in html_content
        assert "class=\"suggestions\"" in html_content

        # Check styling
        assert "<style>" in html_content
        assert "font-family" in html_content
        assert "background-color" in html_content

    def test_s3_storage_mock(self, mock_boto3):
        """Test S3 storage functionality with mocks"""
        report_gen = mock_boto3
        storage_result = report_gen.store_report_in_s3(
            bucket_name="test-bucket",
            report_content="# Test Report",
            report_format="markdown"
        )

        # Since we're using mocks, this should work without actual AWS calls
        assert storage_result["success"] is True
        assert "s3_key" in storage_result

    def test_presigned_url_generation(self, mock_boto3):
        """Test presigned URL generation with mocks"""
        report_gen = mock_boto3
        url_result = report_gen.generate_presigned_download_url(
            bucket_name="test-bucket",
            s3_key="reports/test_report.md"
        )

        assert url_result["success"] is True
        assert "download_url" in url_result
        assert "test-bucket" in url_result["download_url"]

# Demo function (not a test)
def generate_sample_reports():
    """Generate sample report files for manual inspection"""
    # Use pytest-mock to patch boto3.client
    with patch("boto3.client") as mock_client:
        mock_s3 = Mock()
        mock_client.return_value = mock_s3
        mock_s3.put_object.return_value = {"ETag": '"mock-etag"'}
        mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test-key?mock-presigned-params"
        from report_generator import ReportGenerator
        report_gen = ReportGenerator()

        # Generate sample report
        report_result = report_gen.generate_report(
            SAMPLE_ANALYSIS,
            resume_filename="john_doe_resume.pdf",
            job_title="Senior Software Engineer",
        )

        if report_result["success"]:
            # Save sample files
            with open("sample_report.md", "w", encoding="utf-8") as f:
                f.write(report_result["markdown_content"])
            print("✅ Created sample_report.md")

            with open("sample_report.html", "w", encoding="utf-8") as f:
                f.write(report_result["html_content"])
            print("✅ Created sample_report.html")

            # Show preview
            lines = report_result["markdown_content"].split("\n")
            print(f"\n📄 Markdown Report Preview (first 10 lines):")
            for i, line in enumerate(lines[:10]):
                print(f"   {i+1:2d}: {line}")
        else:
            print(f"❌ Report generation failed: {report_result['error']}")

if __name__ == "__main__":
    print("🚀 Running Report Generator Tests")
    print("=" * 50)

    # Run the demo to generate sample files
    generate_sample_reports()

    # You can also run pytest programmatically
    import pytest
    pytest.main([__file__, "-v"])
