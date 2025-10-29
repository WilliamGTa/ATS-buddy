# Requirements Document

## Introduction

ATS Buddy is a simple serverless application that helps job candidates optimize their resumes for Applicant Tracking Systems (ATS). The MVP focuses on core functionality: resume text extraction, AI-powered analysis against job descriptions, and generating actionable improvement reports.

## Requirements

### Requirement 1 - Resume & Job Description Input

**User Story:** As a job candidate, I want to upload my resume and provide a job description, so that the system can analyze them together.

#### Acceptance Criteria

1. WHEN a user uploads a PDF resume THEN the system SHALL extract text using AWS Textract
2. WHEN a user provides job description text THEN the system SHALL accept it for analysis
3. IF upload or extraction fails THEN the system SHALL return simple error messages

### Requirement 2 - Analysis

**User Story:** As a job candidate, I want the system to compare my resume against the job description, so that I can see what's missing and get improvement suggestions.

#### Acceptance Criteria

1. WHEN the system analyzes resume vs job description THEN it SHALL identify missing keywords and skills
2. WHEN analysis completes THEN it SHALL return at least 3 actionable improvement suggestions
3. WHEN keywords are missing THEN it SHALL categorize them (technical skills, soft skills, etc.)

### Requirement 3 - Report Output

**User Story:** As a job candidate, I want to receive a simple report with the analysis results, so that I can easily review and act on the recommendations.

#### Acceptance Criteria

1. WHEN analysis completes THEN the system SHALL generate a report in readable format (Markdown/HTML/text)
2. WHEN the report is ready THEN it SHALL be stored in S3 with a downloadable link
3. WHEN the report is generated THEN it SHALL include missing keywords and improvement suggestions

## Phase 2 Requirements (Future)

### Requirement 4 - API Access (Optional)

**User Story:** As a user, I want simple API access through API Gateway for programmatic use.

### Requirement 5 - Infrastructure as Code (Optional)

**User Story:** As a developer, I want SAM/CloudFormation templates for easy deployment and reproduction.