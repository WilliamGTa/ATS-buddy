"""
Report generator for ATS Buddy analysis results
Formats analysis data into readable reports and handles S3 storage
"""

import boto3
import json
import logging
from datetime import datetime, timezone
from botocore.exceptions import ClientError, BotoCoreError
import uuid

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self):
        """Initialize report generator with S3 client"""
        self.s3 = boto3.client("s3")

    def generate_report(self, analysis_data, resume_filename=None, job_title=None):
        """
        Generate a formatted report from analysis results

        Args:
            analysis_data (dict): Analysis results from Bedrock
            resume_filename (str): Original resume filename (optional)
            job_title (str): Job title from description (optional)

        Returns:
            dict: Contains report content and metadata
        """
        try:
            # Generate report metadata
            report_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)

            # Create both Markdown and HTML versions
            markdown_content = self._generate_markdown_report(
                analysis_data, resume_filename, job_title, timestamp
            )
            html_content = self._generate_html_report(
                analysis_data, resume_filename, job_title, timestamp
            )

            return {
                "success": True,
                "report_id": report_id,
                "timestamp": timestamp.isoformat(),
                "markdown_content": markdown_content,
                "html_content": html_content,
                "metadata": {
                    "resume_filename": resume_filename,
                    "job_title": job_title,
                    "compatibility_score": analysis_data.get("compatibility_score", 0),
                    "missing_keywords_count": len(
                        analysis_data.get("missing_keywords", [])
                    ),
                    "suggestions_count": len(analysis_data.get("suggestions", [])),
                },
            }

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"success": False, "error": "Failed to generate analysis report"}

    def _generate_markdown_report(
        self, analysis_data, resume_filename, job_title, timestamp
    ):
        """Generate Markdown formatted report"""

        # Extract data with defaults
        compatibility_score = analysis_data.get("compatibility_score", 0)
        missing_keywords = analysis_data.get("missing_keywords", [])
        missing_skills = analysis_data.get("missing_skills", {})
        suggestions = analysis_data.get("suggestions", [])
        strengths = analysis_data.get("strengths", [])
        areas_for_improvement = analysis_data.get("areas_for_improvement", [])

        # Build report content
        report_lines = [
            "# ATS Buddy - Resume Analysis Report",
            "",
            f"**Generated:** {timestamp.strftime('%B %d, %Y at %I:%M %p UTC')}",
        ]

        if resume_filename:
            report_lines.append(f"**Resume:** {resume_filename}")
        if job_title:
            report_lines.append(f"**Position:** {job_title}")

        report_lines.extend(
            [
                "",
                "## Compatibility Score",
                "",
                f"**{compatibility_score}%** - ",
            ]
        )

        # Add score interpretation
        if compatibility_score >= 80:
            report_lines.append(
                "**Excellent match!** Your resume aligns very well with the job requirements."
            )
        elif compatibility_score >= 60:
            report_lines.append(
                "**Good match** with room for improvement. Consider the suggestions below."
            )
        else:
            report_lines.append(
                "**Needs improvement** to better match the job requirements."
            )

        report_lines.extend(["", "## Key Findings", ""])

        # Missing Keywords Section
        if missing_keywords:
            report_lines.extend(
                [
                    "### Missing Keywords",
                    "",
                    "The following keywords from the job description were not found in your resume:",
                    "",
                ]
            )
            for keyword in missing_keywords[:10]:  # Limit to top 10
                report_lines.append(f"- {keyword}")
            report_lines.append("")

        # Missing Skills Section
        if missing_skills.get("technical") or missing_skills.get("soft"):
            report_lines.extend(["### Missing Skills", ""])

            if missing_skills.get("technical"):
                report_lines.extend(["**Technical Skills:**"])
                for skill in missing_skills["technical"][:8]:  # Limit to top 8
                    report_lines.append(f"- {skill}")
                report_lines.append("")

            if missing_skills.get("soft"):
                report_lines.extend(["**Soft Skills:**"])
                for skill in missing_skills["soft"][:6]:  # Limit to top 6
                    report_lines.append(f"- {skill}")
                report_lines.append("")

        # Strengths Section
        if strengths:
            report_lines.extend(
                [
                    "## Your Strengths",
                    "",
                    "Areas where your resume already aligns well:",
                    "",
                ]
            )
            for strength in strengths[:5]:  # Limit to top 5
                report_lines.append(f"- {strength}")
            report_lines.append("")

        # Improvement Suggestions
        if suggestions:
            report_lines.extend(
                [
                    "## Actionable Recommendations",
                    "",
                    "Here are specific ways to improve your resume for this position:",
                    "",
                ]
            )
            for i, suggestion in enumerate(suggestions, 1):
                report_lines.append(f"{i}. {suggestion}")
            report_lines.append("")

        # Areas for Improvement
        if areas_for_improvement:
            report_lines.extend(["## Areas for Improvement", ""])
            for area in areas_for_improvement[:5]:  # Limit to top 5
                report_lines.append(f"- {area}")
            report_lines.append("")

        # Footer
        report_lines.extend(
            [
                "---",
                "",
                "## Next Steps",
                "",
                "1. **Review missing keywords** and incorporate relevant ones naturally into your resume",
                "2. **Update your skills section** to include missing technical and soft skills you possess",
                "3. **Quantify your achievements** with specific metrics and numbers where possible",
                "4. **Tailor your experience descriptions** to use language similar to the job posting",
                "5. **Proofread carefully** to ensure your resume is error-free and professional",
                "",
                "*Generated by ATS Buddy - Your AI-powered resume optimization assistant*",
            ]
        )

        return "\n".join(report_lines)

    def _generate_html_report(
        self, analysis_data, resume_filename, job_title, timestamp
    ):
        """Generate HTML formatted report"""

        # Extract data with defaults
        compatibility_score = analysis_data.get("compatibility_score", 0)
        missing_keywords = analysis_data.get("missing_keywords", [])
        missing_skills = analysis_data.get("missing_skills", {})
        suggestions = analysis_data.get("suggestions", [])
        strengths = analysis_data.get("strengths", [])
        areas_for_improvement = analysis_data.get("areas_for_improvement", [])

        # Determine score color and message
        if compatibility_score >= 80:
            score_color = "#22c55e"  # Green
            score_message = "Excellent match! Your resume aligns very well with the job requirements."
        elif compatibility_score >= 60:
            score_color = "#eab308"  # Yellow
            score_message = "Good match with room for improvement. Consider the suggestions below."
        else:
            score_color = "#ef4444"  # Red
            score_message = "Needs improvement to better match the job requirements."

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATS Buddy - Resume Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #1e293b;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #374151;
            margin-top: 30px;
        }}
        h3 {{
            color: #4b5563;
        }}
        .score-section {{
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .score-number {{
            font-size: 3em;
            font-weight: bold;
            color: {score_color};
        }}
        .score-message {{
            font-size: 1.1em;
            margin-top: 10px;
        }}
        .metadata {{
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin: 20px 0;
        }}
        .metadata strong {{
            color: #1e293b;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .suggestions {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
        }}
        .strengths {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 15px;
            margin: 15px 0;
        }}
        .missing {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin: 15px 0;
        }}
        .next-steps {{
            background: #e0f2fe;
            border-left: 4px solid #0284c7;
            padding: 15px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ATS Buddy - Resume Analysis Report</h1>
        
        <div class="metadata">
            <strong>Generated:</strong> {timestamp.strftime('%B %d, %Y at %I:%M %p UTC')}<br>
"""

        if resume_filename:
            html_content += (
                f"            <strong>Resume:</strong> {resume_filename}<br>\n"
            )
        if job_title:
            html_content += f"            <strong>Position:</strong> {job_title}<br>\n"

        html_content += f"""        </div>
        
        <div class="score-section">
            <h2>Compatibility Score</h2>
            <div class="score-number">{compatibility_score}%</div>
            <div class="score-message">{score_message}</div>
        </div>
"""

        # Missing Keywords Section
        if missing_keywords:
            html_content += """
        <h2>Missing Keywords</h2>
        <div class="missing">
            <p>The following keywords from the job description were not found in your resume:</p>
            <ul>
"""
            for keyword in missing_keywords[:10]:  # Limit to top 10
                html_content += f"                <li>{keyword}</li>\n"
            html_content += "            </ul>\n        </div>\n"

        # Missing Skills Section
        if missing_skills.get("technical") or missing_skills.get("soft"):
            html_content += """
        <h2>Missing Skills</h2>
        <div class="missing">
"""

            if missing_skills.get("technical"):
                html_content += (
                    "            <h3>Technical Skills:</h3>\n            <ul>\n"
                )
                for skill in missing_skills["technical"][:8]:  # Limit to top 8
                    html_content += f"                <li>{skill}</li>\n"
                html_content += "            </ul>\n"

            if missing_skills.get("soft"):
                html_content += "            <h3>Soft Skills:</h3>\n            <ul>\n"
                for skill in missing_skills["soft"][:6]:  # Limit to top 6
                    html_content += f"                <li>{skill}</li>\n"
                html_content += "            </ul>\n"

            html_content += "        </div>\n"

        # Strengths Section
        if strengths:
            html_content += """
        <h2>Your Strengths</h2>
        <div class="strengths">
            <p>Areas where your resume already aligns well:</p>
            <ul>
"""
            for strength in strengths[:5]:  # Limit to top 5
                html_content += f"                <li>{strength}</li>\n"
            html_content += "            </ul>\n        </div>\n"

        # Improvement Suggestions
        if suggestions:
            html_content += """
        <h2>Actionable Recommendations</h2>
        <div class="suggestions">
            <p>Here are specific ways to improve your resume for this position:</p>
            <ol>
"""
            for suggestion in suggestions:
                html_content += f"                <li>{suggestion}</li>\n"
            html_content += "            </ol>\n        </div>\n"

        # Areas for Improvement
        if areas_for_improvement:
            html_content += """
        <h2>Areas for Improvement</h2>
        <div class="missing">
            <ul>
"""
            for area in areas_for_improvement[:5]:  # Limit to top 5
                html_content += f"                <li>{area}</li>\n"
            html_content += "            </ul>\n        </div>\n"

        # Next Steps
        html_content += """
        <h2>Next Steps</h2>
        <div class="next-steps">
            <ol>
                <li><strong>Review missing keywords</strong> and incorporate relevant ones naturally into your resume</li>
                <li><strong>Update your skills section</strong> to include missing technical and soft skills you possess</li>
                <li><strong>Quantify your achievements</strong> with specific metrics and numbers where possible</li>
                <li><strong>Tailor your experience descriptions</strong> to use language similar to the job posting</li>
                <li><strong>Proofread carefully</strong> to ensure your resume is error-free and professional</li>
            </ol>
        </div>
        
        <div class="footer">
            Generated by ATS Buddy - Your AI-powered resume optimization assistant
        </div>
    </div>
</body>
</html>"""

        return html_content

    def store_report_in_s3(
        self, bucket_name, report_content, report_format="markdown", report_id=None
    ):
        """
        Store generated report in S3 bucket

        Args:
            bucket_name (str): S3 bucket name for report storage
            report_content (str): Report content to store
            report_format (str): Format type ('markdown' or 'html')
            report_id (str): Unique report identifier (optional)

        Returns:
            dict: Contains S3 key and storage status
        """
        try:
            # Generate unique S3 key
            if not report_id:
                report_id = str(uuid.uuid4())

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            file_extension = "md" if report_format == "markdown" else "html"
            s3_key = f"reports/{timestamp}_{report_id}.{file_extension}"

            # Set content type
            content_type = (
                "text/markdown" if report_format == "markdown" else "text/html"
            )

            # Upload to S3
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=report_content.encode("utf-8"),
                ContentType=content_type,
                Metadata={
                    "report-id": report_id,
                    "format": report_format,
                    "generated-at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(f"Report stored successfully: s3://{bucket_name}/{s3_key}")

            return {
                "success": True,
                "s3_key": s3_key,
                "bucket_name": bucket_name,
                "report_id": report_id,
                "format": report_format,
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "AccessDenied":
                return {
                    "success": False,
                    "error": "Access denied to S3 bucket. Check IAM permissions.",
                }
            elif error_code == "NoSuchBucket":
                return {"success": False, "error": "S3 bucket does not exist."}
            else:
                logger.error(f"S3 ClientError: {error_code} - {e}")
                return {"success": False, "error": "Failed to store report in S3."}

        except Exception as e:
            logger.error(f"Unexpected error storing report: {e}")
            return {"success": False, "error": "Unexpected error storing report."}

    def generate_presigned_download_url(self, bucket_name, s3_key, expiration=3600):
        """
        Generate presigned URL for report download

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

            return {
                "success": True,
                "download_url": url,
                "expires_in": expiration,
                "expires_at": (datetime.now(timezone.utc).timestamp() + expiration),
            }

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return {"success": False, "error": "Failed to generate download URL"}
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return {
                "success": False,
                "error": "Unexpected error generating download URL",
            }

    def create_complete_report_package(
        self, analysis_data, bucket_name, resume_filename=None, job_title=None
    ):
        """
        Generate complete report package with both formats and S3 storage

        Args:
            analysis_data (dict): Analysis results from Bedrock
            bucket_name (str): S3 bucket for report storage
            resume_filename (str): Original resume filename (optional)
            job_title (str): Job title from description (optional)

        Returns:
            dict: Complete report package with download URLs
        """
        try:
            # Generate report content
            report_result = self.generate_report(
                analysis_data, resume_filename, job_title
            )
            if not report_result["success"]:
                return report_result

            report_id = report_result["report_id"]

            # Store both formats in S3
            markdown_storage = self.store_report_in_s3(
                bucket_name, report_result["markdown_content"], "markdown", report_id
            )

            html_storage = self.store_report_in_s3(
                bucket_name, report_result["html_content"], "html", report_id
            )

            if not markdown_storage["success"] or not html_storage["success"]:
                return {"success": False, "error": "Failed to store reports in S3"}

            # Generate download URLs
            markdown_url = self.generate_presigned_download_url(
                bucket_name, markdown_storage["s3_key"]
            )
            html_url = self.generate_presigned_download_url(
                bucket_name, html_storage["s3_key"]
            )

            if not markdown_url["success"] or not html_url["success"]:
                return {"success": False, "error": "Failed to generate download URLs"}

            return {
                "success": True,
                "report_id": report_id,
                "timestamp": report_result["timestamp"],
                "metadata": report_result["metadata"],
                "reports": {
                    "markdown": {
                        "s3_key": markdown_storage["s3_key"],
                        "download_url": markdown_url["download_url"],
                        "expires_at": markdown_url["expires_at"],
                    },
                    "html": {
                        "s3_key": html_storage["s3_key"],
                        "download_url": html_url["download_url"],
                        "expires_at": html_url["expires_at"],
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error creating complete report package: {e}")
            return {
                "success": False,
                "error": "Failed to create complete report package",
            }
