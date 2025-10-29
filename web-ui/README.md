# Web UI for ATS Buddy

A responsive web interface for the ATS Buddy resume analysis system that allows users to upload resumes, enter job descriptions, and receive detailed compatibility analysis.

## Features

- **File Upload**: Drag-and-drop or click to upload PDF resumes (max 10MB)
- **Job Description Input**: Text area with validation (minimum 100 characters)
- **Real-time Analysis**: Progress tracking with animated loading states
- **Detailed Results**: Compatibility score, missing keywords, skills gaps, and suggestions
- **Report Downloads**: Access to HTML and Markdown reports
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: User-friendly error messages and retry options

## Setup

### 1. Configure API Gateway URL

Update the API Gateway URL in `index.html`:

```javascript
window.ATS_BUDDY_CONFIG = {
    apiUrl: 'https://your-actual-api-gateway-url.execute-api.region.amazonaws.com/dev/analyze'
};
```

To get your API Gateway URL:
1. Deploy the ATS Buddy Lambda function with SAM
2. Check the CloudFormation outputs for `ApiGatewayUrl`
3. The URL format is: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/analyze`

### 2. Serve the Web Files

Using Python:
```bash
cd web-ui
python -m http.server 8000
```

Using Node.js:
```bash
cd web-ui
npx serve .
```

Using any other web server (Apache, Nginx, etc.)

### 3. Access the Application

Open http://localhost:8000 in your browser

## Usage

### Step 1: Upload Resume
- Click the upload area or drag and drop a PDF file
- Maximum file size: 10MB
- Only PDF files are accepted
- File validation happens immediately

### Step 2: Enter Job Description
- Paste or type the job description
- Minimum 100 characters required
- Character count is displayed in real-time
- Auto-expanding text area

### Step 3: Analyze
- Click "Analyze Resume" when both fields are valid
- Progress tracking shows three stages:
  1. Extracting text from PDF
  2. Analyzing against job requirements
  3. Generating compatibility report

### Step 4: View Results
- **Compatibility Score**: 0-100% with color-coded rating
- **Missing Keywords**: Important terms not found in resume
- **Missing Skills**: Technical and soft skills gaps
- **Suggestions**: Actionable recommendations for improvement
- **Strengths**: Positive aspects of the resume
- **Download Reports**: HTML and Markdown format reports

### Step 5: New Analysis
- Click "Analyze Another Resume" to start over
- Form resets completely for new analysis

## API Integration

The web UI integrates with the ATS Buddy Lambda function through API Gateway using:

- **Endpoint**: POST `/analyze`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `resume`: PDF file
  - `jobDescription`: Text (minimum 50 characters for API, 100 for UI)

### Response Format
```json
{
  "sessionId": "uuid-string",
  "compatibilityScore": 75,
  "missingKeywords": ["Docker", "Kubernetes"],
  "missingSkills": {
    "technical": ["Docker", "Kubernetes"],
    "soft": ["leadership"]
  },
  "suggestions": ["Add Docker experience..."],
  "strengths": ["Strong Python background..."],
  "reports": {
    "html": { "downloadUrl": "...", "expiresAt": "..." },
    "markdown": { "downloadUrl": "...", "expiresAt": "..." }
  }
}
```

## Error Handling

The UI handles various error scenarios:

- **File Validation**: Invalid file type or size
- **Network Errors**: Connection issues with retry capability
- **API Errors**: Server-side processing failures
- **Timeout Errors**: Long-running analysis timeouts

All errors display user-friendly messages with guidance on resolution.

## Browser Compatibility

- Modern browsers with ES6+ support
- Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- Mobile browsers on iOS Safari and Chrome Mobile

## Development

### File Structure
```
web-ui/
├── index.html          # Main HTML page
├── script.js           # JavaScript functionality
├── styles.css          # CSS styles and responsive design
└── README.md          # This documentation
```

### Key JavaScript Functions
- `startAnalysis()`: Handles form submission and API calls
- `showLoadingState()`: Creates animated progress indicators
- `showAnalysisResults()`: Displays formatted results
- `startNewAnalysis()`: Resets form for new analysis

### CSS Classes
- `.loading-section`: Animated progress display
- `.results-section`: Results container with gradient background
- `.compatibility-score`: Score circle with color coding
- `.result-item`: Individual result components

## Publishing Changes to AWS S3

The ATS Buddy infrastructure creates an S3 bucket for hosting the web UI. To publish your latest changes:

### 1. Get the Web UI Bucket Name

From your CloudFormation stack outputs:
```bash
aws cloudformation describe-stacks --stack-name ats-buddy-dev --region ap-southeast-1 --query "Stacks[0].Outputs[?OutputKey=='WebUIBucketName'].OutputValue" --output text
```

Or check the deployment output after running `sam deploy`.

### 2. Upload Files to S3

Upload all web-ui files to the S3 bucket:

```bash
# Navigate to web-ui directory
cd web-ui

# Upload all files (replace bucket name with your actual bucket)
aws s3 sync . s3://ats-buddy-web-ui-dev-123456789 --delete

# Or upload individual files
aws s3 cp index.html s3://ats-buddy-web-ui-dev-123456789/
aws s3 cp script.js s3://ats-buddy-web-ui-dev-123456789/
aws s3 cp styles.css s3://ats-buddy-web-ui-dev-123456789/
```

### 3. Set Proper Content Types (Optional)

Ensure proper MIME types for better browser handling:

```bash
# Set content type for HTML files
aws s3 cp index.html s3://ats-buddy-web-ui-dev-123456789/ --content-type "text/html"

# Set content type for CSS files
aws s3 cp styles.css s3://ats-buddy-web-ui-dev-123456789/ --content-type "text/css"

# Set content type for JavaScript files
aws s3 cp script.js s3://ats-buddy-web-ui-dev-123456789/ --content-type "application/javascript"
```

### 4. Access Your Updated Web UI

Your web UI will be available at:
```
http://ats-buddy-web-ui-dev-123456789.s3-website-ap-southeast-1.amazonaws.com
```

### 5. Automated Deployment Script

Create a deployment script `deploy-web-ui.sh`:

```bash
#!/bin/bash

# Get the bucket name from CloudFormation
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name ats-buddy-dev \
  --region ap-southeast-1 \
  --query "Stacks[0].Outputs[?OutputKey=='WebUIBucketName'].OutputValue" \
  --output text)

if [ -z "$BUCKET_NAME" ]; then
  echo "Error: Could not get bucket name from CloudFormation stack"
  exit 1
fi

echo "Deploying web UI to bucket: $BUCKET_NAME"

# Upload files with proper content types
aws s3 cp index.html s3://$BUCKET_NAME/ --content-type "text/html"
aws s3 cp script.js s3://$BUCKET_NAME/ --content-type "application/javascript"
aws s3 cp styles.css s3://$BUCKET_NAME/ --content-type "text/css"

# Upload any other files
aws s3 sync . s3://$BUCKET_NAME/ --exclude "*.sh" --exclude "README.md" --exclude ".git*"

echo "Deployment complete!"
echo "Web UI available at: http://$BUCKET_NAME.s3-website-ap-southeast-1.amazonaws.com"
```

Make it executable and run:
```bash
chmod +x deploy-web-ui.sh
./deploy-web-ui.sh
```

### 6. Quick Update Commands

For quick updates after making changes:

```bash
# Update just the HTML (most common)
aws s3 cp index.html s3://$(aws cloudformation describe-stacks --stack-name ats-buddy-dev --region ap-southeast-1 --query "Stacks[0].Outputs[?OutputKey=='WebUIBucketName'].OutputValue" --output text)/ --content-type "text/html"

# Update all files
aws s3 sync . s3://$(aws cloudformation describe-stacks --stack-name ats-buddy-dev --region ap-southeast-1 --query "Stacks[0].Outputs[?OutputKey=='WebUIBucketName'].OutputValue" --output text)/ --exclude "*.md" --exclude "*.sh"
```

### 7. Verify Deployment

Check that your files were uploaded correctly:
```bash
aws s3 ls s3://ats-buddy-web-ui-dev-123456789/
```

## Deployment Options

### Static Website Hosting
- AWS S3 + CloudFront (configured by default)
- Netlify
- Vercel
- GitHub Pages

### Web Server
- Apache HTTP Server
- Nginx
- IIS

### CDN Integration
For production, consider using CloudFront distribution for faster global access and caching of static assets.

## Security Considerations

- All API calls use HTTPS in production
- No sensitive data stored in browser localStorage
- File uploads are validated client-side and server-side
- CORS properly configured on API Gateway
- Input sanitization for job description text

## Troubleshooting

### Common Issues

1. **API Gateway URL not working**
   - Verify the URL in `index.html` configuration
   - Check that Lambda function is deployed
   - Ensure CORS is enabled on API Gateway

2. **File upload fails**
   - Check file size (max 10MB)
   - Ensure file is PDF format
   - Verify network connection

3. **Analysis takes too long**
   - Normal processing time is 10-30 seconds
   - Check Lambda function logs for errors
   - Verify Textract and Bedrock services are available

4. **Results not displaying**
   - Check browser console for JavaScript errors
   - Verify API response format matches expected structure
   - Ensure all required fields are present in response

### Getting Help

- Check browser developer console for errors
- Review Lambda function CloudWatch logs
- Test API endpoint directly with curl or Postman
- Verify SAM template deployment was successful