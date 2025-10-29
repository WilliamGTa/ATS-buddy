# Design Document

## Overview

ATS Buddy is a serverless AWS application that analyzes resumes against job descriptions to help candidates optimize for ATS systems. The system uses a simple pipeline: S3 storage → Textract extraction → Bedrock AI analysis → report generation.

## Architecture

### High-Level Flow
```
User → S3 (PDF) → Lambda → Textract → Bedrock → S3 (Report) → User
```

### AWS Services
- **S3**: Resume storage and report output
- **Lambda**: Orchestration and processing logic
- **Textract**: PDF text extraction
- **Bedrock**: AI analysis (Claude/Nova models)
- **API Gateway**: Optional HTTP interface

### Core Components
1. **Input Handler**: Manages resume uploads and job description input
2. **Text Extractor**: Interfaces with Textract for PDF processing
3. **AI Analyzer**: Bedrock integration for resume analysis
4. **Report Generator**: Creates and stores formatted output

## Components and Interfaces

### Lambda Function Structure
```
ats-buddy-processor/
├── handler.py          # Main Lambda entry point
├── textract_client.py  # Textract integration
├── bedrock_client.py   # Bedrock AI analysis
├── report_generator.py # Output formatting
└── requirements.txt    # Dependencies
```

### Input Interface
```json
{
  "resume_s3_key": "resumes/user123/resume.pdf",
  "job_description": "Software Engineer position requiring Python, AWS, Docker..."
}
```

### Bedrock Analysis Prompt
```
Compare this resume against the job description and return JSON:

Resume: {extracted_text}
Job Description: {job_description}

Return format:
{
  "missing_keywords": ["keyword1", "keyword2"],
  "missing_skills": {
    "technical": ["Docker", "Kubernetes"],
    "soft": ["leadership", "communication"]
  },
  "suggestions": [
    "Add Docker experience to your technical skills section",
    "Quantify your achievements with specific metrics",
    "Include cloud platform experience in project descriptions"
  ],
  "compatibility_score": 75
}
```

### Output Interface
```json
{
  "analysis_complete": true,
  "report_s3_key": "reports/user123/analysis_report.md",
  "download_url": "https://s3.amazonaws.com/bucket/reports/...",
  "summary": {
    "missing_keywords": 5,
    "suggestions_count": 3,
    "compatibility_score": 75
  }
}
```

## Data Models

The analysis output will include missing keywords, categorized skills (technical/soft), improvement suggestions, and a compatibility score. Reports will contain metadata like timestamps and S3 storage keys for tracking.

## Error Handling

Simple error handling for MVP:
- **Textract Failures**: Return "PDF processing failed" message
- **Bedrock Failures**: Return "Analysis service unavailable" message  
- **S3 Failures**: Return "File upload/download failed" message

## Testing Strategy

### MVP Testing Approach
Manual testing with sample data:
```
samples/
├── resumes/
│   ├── software_engineer.pdf
│   └── data_scientist.pdf
└── job_descriptions/
    ├── backend_engineer.txt
    └── frontend_developer.txt
```

**Test Flow**: Sample PDF → Textract → Bedrock → Report generation → Verify expected output

### Security (Hackathon Level)
- **S3 Buckets**: Private with presigned URLs for report downloads
- **Basic IAM**: Lambda execution role with S3, Textract, Bedrock permissions