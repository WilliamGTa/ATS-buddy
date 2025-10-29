# Requirements Document (Refined for Hackathon POC)

## Introduction

The Resume Optimization Platform enhances the existing ATS Buddy system by adding intelligent file management, persistent storage (temporary), and AI-powered resume generation capabilities. This platform transforms the current one-time analysis tool into a resume optimization service that eliminates redundant processing, provides resume previews, and generates enhanced resumes based on AI recommendations. This version is simplified for a proof-of-concept and does not include user session management.

## Core Requirements (Focus for Hackathon)

### Requirement 1 - Intelligent File Management with Hash-Based Deduplication

**User Story:** As a job candidate, I want the system to recognize when I upload the same PDF file, so that I don't waste storage space and processing time on duplicate uploads within the current session.

#### Acceptance Criteria

1. WHEN a user uploads a PDF file THEN the system SHALL calculate a SHA-256 hash of the file content
2. WHEN the hash is calculated THEN the system SHALL check if a file with the same hash already exists in the database
3. IF a file with the same hash exists THEN the system SHALL skip the upload and Textract processing and use the existing extracted text
4. IF the file hash is unique THEN the system SHALL proceed with normal upload and Textract processing
5. WHEN using existing file data THEN the system SHALL display a message indicating "Resume already processed - using existing data"
6. WHEN file deduplication occurs THEN the system SHALL reduce processing time compared to full processing

### Requirement 2 - Temporary Database Storage with AWS Services

**User Story:** As a job candidate, I want my resume data to be stored temporarily, so that it is not re-processed when I am in the middle of an analysis.

#### Acceptance Criteria

1. WHEN the system processes a resume THEN it SHALL store the file hash, original filename, extracted text, and upload timestamp in DynamoDB
2. WHEN an analysis is completed THEN the system SHALL store the job description and analysis results in DynamoDB
3. WHEN storing data THEN the system SHALL use DynamoDB as the primary database for structured data and metadata
4. WHEN storing files THEN the system SHALL continue using S3 for PDF file storage and generated reports
5. WHEN data is stored THEN the system SHALL implement a data retention policy (TTL, configurable, 7 days by default). This is needed to clear up space.

### Requirement 3 - Resume Preview

**User Story:** As a job candidate, I want to preview my uploaded resume, so that I can verify the correct document was processed.

#### Acceptance Criteria

1. WHEN a user uploads a resume THEN the system SHALL display a preview of the extracted text in a readable format
2. WHEN displaying the preview THEN the system SHALL show the original filename, upload date, and file size

### Requirement 4 - AI-Powered Resume Enhancement Generation

**User Story:** As a job candidate, I want the system to generate an enhanced version of my resume based on the analysis recommendations, so that I can have a more competitive resume for specific job applications.

#### Acceptance Criteria

1. WHEN an analysis is completed THEN the system SHALL offer an option to "Generate Enhanced Resume"
2. WHEN generating enhanced resume THEN the system SHALL use Amazon Bedrock to create an improved version incorporating the recommendations
3. WHEN creating enhanced resume THEN the system SHALL maintain the original structure while adding missing keywords and improving descriptions
4. WHEN enhanced resume is generated THEN the system SHALL present it in a formatted text output that users can copy and edit
5. WHEN displaying enhanced resume THEN the system SHALL highlight the specific improvements made (added keywords, enhanced descriptions, etc.)

### Requirement 5 - Cost and Performance Optimization

**User Story:** As a system operator, I want to minimize AWS service costs and improve response times, so that the platform is economically sustainable and provides fast user experience.

#### Acceptance Criteria

1. WHEN implementing deduplication THEN the system SHALL reduce Textract API calls for repeat uploads within a short time period
2. WHEN using cached data THEN the system SHALL respond to analysis requests faster than cold processing
3. WHEN storing data THEN the system SHALL optimize DynamoDB usage for minimal read/write operations

### Requirement 6 - Web UI for Core Features

**User Story:** As a job candidate, I want a web interface that supports the core features, so that I can easily upload resumes, enter job descriptions, and generate enhanced resumes.

#### Acceptance Criteria

1. WHEN accessing the web UI THEN it SHALL display a form for resume upload and job description entry
2. WHEN uploading files THEN the system SHALL show deduplication status if it occurs
3. WHEN generating enhanced resumes THEN the UI SHALL display the enhanced content with highlighting of improvements
4. WHEN displaying analysis results THEN the UI SHALL offer prominent "Generate Enhanced Resume" option

## Removed Requirements (Out of Scope for Hackathon)

- **Requirement 5 - Iterative Resume Refinement Workflow** (Complex version management)
- **Requirement 6 - Enhanced User Session Management** (No user accounts or persistent sessions)
- **Requirement 8 - Enhanced Web UI for New Features** (Only the basic form UI is needed)