# Design Document

## Overview

The Web UI Interface provides a modern, responsive web application that serves as the frontend for the existing ATS Buddy system. It creates a seamless user experience by integrating with the current AWS backend through API Gateway, allowing users to upload resumes, enter job descriptions, and view analysis reports in real-time.

## Architecture

### High-Level Flow
```
User Browser → Static Web App (S3/CloudFront) → API Gateway → Lambda → Existing ATS Backend
```

### Updated System Architecture
```
Frontend:     React/Vue SPA hosted on S3 + CloudFront
API Layer:    API Gateway with CORS enabled
Backend:      Existing Lambda functions (enhanced with API endpoints)
Storage:      S3 for resumes, reports, and static web assets
```

### Integration Points
- **File Upload**: Direct to S3 with presigned URLs from API Gateway
- **Analysis Trigger**: REST API call to enhanced Lambda handler
- **Status Polling**: WebSocket or polling endpoint for real-time updates
- **Report Retrieval**: Presigned S3 URLs for secure report access

## Components and Interfaces

### Frontend Architecture
```
web-ui/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── FileUpload.js       # Resume upload component
│   │   ├── JobDescription.js   # Job description input
│   │   ├── AnalysisStatus.js   # Progress tracking
│   │   └── ReportViewer.js     # Results display
│   ├── services/
│   │   ├── apiClient.js        # API Gateway integration
│   │   └── s3Upload.js         # Direct S3 upload handling
│   ├── utils/
│   │   └── validation.js       # Input validation
│   └── App.js                  # Main application
└── package.json
```

### API Gateway Endpoints
```
POST /api/upload-url          # Get presigned URL for resume upload
POST /api/analyze             # Trigger analysis with resume key + job description
GET  /api/status/{sessionId}  # Check analysis progress
GET  /api/report/{sessionId}  # Get analysis results
```

### Enhanced Lambda Handler Interface
```python
# New API endpoints added to existing handler.py
def api_handler(event, context):
    route = event['routeKey']
    
    if route == 'POST /upload-url':
        return generate_presigned_upload_url()
    elif route == 'POST /analyze':
        return start_analysis(event['body'])
    elif route == 'GET /status/{sessionId}':
        return get_analysis_status(event['pathParameters']['sessionId'])
    elif route == 'GET /report/{sessionId}':
        return get_analysis_report(event['pathParameters']['sessionId'])
```

### Data Flow Interfaces

#### Upload Flow
```json
// 1. Request presigned URL
POST /api/upload-url
Response: {
  "uploadUrl": "https://s3.amazonaws.com/bucket/presigned-url",
  "fileKey": "resumes/session123/resume.pdf",
  "sessionId": "session123"
}

// 2. Direct upload to S3 (from browser)
PUT {uploadUrl} with PDF file

// 3. Trigger analysis
POST /api/analyze
{
  "sessionId": "session123",
  "fileKey": "resumes/session123/resume.pdf",
  "jobDescription": "Software Engineer position..."
}
```

#### Analysis Status Interface
```json
GET /api/status/session123
Response: {
  "status": "processing",
  "stage": "text_extraction", // text_extraction, ai_analysis, report_generation, complete
  "progress": 33,
  "message": "Extracting text from PDF...",
  "estimatedTimeRemaining": 45
}
```

#### Report Interface
```json
GET /api/report/session123
Response: {
  "status": "complete",
  "report": {
    "compatibilityScore": 75,
    "missingKeywords": ["Docker", "Kubernetes", "CI/CD"],
    "missingSkills": {
      "technical": ["Docker", "Kubernetes"],
      "soft": ["leadership", "communication"]
    },
    "suggestions": [
      "Add Docker experience to your technical skills section",
      "Quantify your achievements with specific metrics"
    ]
  },
  "downloadUrl": "https://s3.amazonaws.com/bucket/reports/session123/report.pdf",
  "shareableUrl": "https://app.atsbuddy.com/shared/abc123def456"
}
```

## User Interface Design

### Layout Structure
```
Header: ATS Buddy logo + navigation
Main Content:
  ├── Step 1: Upload Resume (drag-drop + file picker)
  ├── Step 2: Enter Job Description (expandable textarea)
  ├── Step 3: Analyze (prominent CTA button)
  └── Step 4: Results (collapsible report viewer)
Footer: Links + hackathon attribution
```

### Component Specifications

#### FileUpload Component
- Drag-and-drop zone with visual feedback
- File type validation (PDF only, max 10MB)
- Upload progress bar with percentage
- Error handling for invalid files
- Preview of selected file name

#### JobDescription Component
- Auto-expanding textarea (min 3 lines, max 20 lines)
- Character count indicator (minimum 100 characters)
- Paste detection with formatting cleanup
- Sample job description link for demo purposes

#### AnalysisStatus Component
- Multi-stage progress indicator (4 stages)
- Animated loading spinner
- Descriptive status messages
- Estimated time remaining
- Cancel analysis option

#### ReportViewer Component
- Compatibility score with visual gauge (0-100)
- Categorized missing keywords with color coding
- Expandable suggestions list with action items
- Download and share buttons
- "Start New Analysis" reset button

## Error Handling

### Frontend Error States
- **Network Errors**: Retry mechanism with exponential backoff
- **File Upload Errors**: Clear messaging for file type/size issues
- **API Errors**: User-friendly error messages with support contact
- **Timeout Errors**: Option to check status manually or restart

### Backend Error Integration
- Map existing Lambda error codes to user-friendly messages
- Implement circuit breaker pattern for external service failures
- Add request ID tracking for debugging support issues

## Testing Strategy

### Frontend Testing
```
tests/
├── unit/
│   ├── FileUpload.test.js
│   ├── JobDescription.test.js
│   └── ReportViewer.test.js
├── integration/
│   └── api-integration.test.js
└── e2e/
    └── complete-workflow.test.js
```

### API Testing
- Test all endpoints with valid/invalid inputs
- Verify CORS headers for cross-origin requests
- Load testing with concurrent file uploads
- Security testing for presigned URL expiration

## Security Considerations

### Frontend Security
- Input sanitization for job description text
- File type validation before upload
- HTTPS enforcement for all API calls
- No sensitive data stored in browser localStorage

### API Security
- CORS configuration for specific domains
- Rate limiting on API Gateway endpoints
- Presigned URL expiration (15 minutes for uploads)
- Session-based access control for reports

### Data Privacy
- Temporary file storage (auto-delete after 24 hours)
- No personal data logging in CloudWatch
- Shareable links with expiration and unique tokens
- Option for users to delete their data immediately

## Deployment Architecture

### Static Website Hosting
```
S3 Bucket (web-ui-assets) → CloudFront Distribution → Custom Domain
```

### Infrastructure Updates
```yaml
# Additional SAM template resources
WebUIBucket:
  Type: AWS::S3::Bucket
  Properties:
    WebsiteConfiguration:
      IndexDocument: index.html

APIGateway:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    ProtocolType: HTTP
    CorsConfiguration:
      AllowOrigins: ["https://atsbuddy.com"]
      AllowMethods: ["GET", "POST", "OPTIONS"]
      AllowHeaders: ["Content-Type", "Authorization"]

CloudFrontDistribution:
  Type: AWS::CloudFront::Distribution
  Properties:
    DistributionConfig:
      Origins:
        - DomainName: !GetAtt WebUIBucket.DomainName
          Id: S3Origin
```

## Performance Optimization

### Frontend Performance
- Code splitting for faster initial load
- Image optimization and lazy loading
- Service worker for offline capability
- CDN caching for static assets

### Backend Performance
- API Gateway caching for status endpoints
- Lambda provisioned concurrency for faster cold starts
- S3 Transfer Acceleration for large file uploads
- CloudFront edge locations for global performance