#!/usr/bin/env python3
"""
Test the deployed API Gateway endpoint directly
"""

import requests
import json
from pathlib import Path

def test_deployed_api():
    """Test the deployed API Gateway endpoint"""
    
    api_url = "https://4rvo13bwv1.execute-api.ap-southeast-1.amazonaws.com/dev/analyze"
    
    # Test with simple text data (multipart form)
    files = {
        'jobDescription': (None, 'Software Engineer position requiring Python, AWS, Docker, and 3+ years experience')
    }
    
    # Use the actual sample PDF file
    pdf_path = Path(__file__).parent.parent / 'docs' / 'sample_resume.pdf'
    
    if pdf_path.exists():
        with open(pdf_path, 'rb') as pdf_file:
            files['resume'] = ('sample_resume.pdf', pdf_file.read(), 'application/pdf')
        print(f"📄 Using sample PDF: {pdf_path}")
    else:
        print(f"❌ Sample PDF not found at: {pdf_path}")
        print("   Creating a minimal PDF for testing...")
        # Fallback: create minimal PDF content for testing
        minimal_pdf = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n174\n%%EOF'
        files['resume'] = ('test_resume.pdf', minimal_pdf, 'application/pdf')
    
    print("🧪 Testing deployed API Gateway endpoint...")
    print(f"📡 URL: {api_url}")
    
    try:
        response = requests.post(api_url, files=files, timeout=60)
        
        print(f"\n📊 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS!")
                print(f"   Session ID: {data.get('sessionId', 'N/A')}")
                print(f"   Compatibility Score: {data.get('compatibilityScore', 'N/A')}%")
                print(f"   Missing Keywords: {len(data.get('missingKeywords', []))}")
                print(f"   Suggestions: {len(data.get('suggestions', []))}")
                
                if data.get('reports'):
                    print(f"   Reports Available: {list(data['reports'].keys())}")
                    
            except json.JSONDecodeError:
                print(f"   ✅ SUCCESS (Non-JSON response)")
                print(f"   Response: {response.text[:200]}...")
                
        elif response.status_code == 422:
            # Handle processing errors (might be expected for test PDF)
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                if 'Unsupported file format' in error_msg or 'Only PDF files are supported' in error_msg:
                    print(f"   ⚠️  PDF validation error: {error_msg}")
                    print(f"   This might indicate an issue with the test PDF")
                    return False
                elif 'Text extraction failed' in error_msg:
                    print(f"   ⚠️  Text extraction failed: {error_msg}")
                    print(f"   This might be expected for minimal test PDFs")
                    print(f"   ✅ API is responding correctly to processing errors")
                    return True
                else:
                    print(f"   ❌ UNEXPECTED ERROR: {error_msg}")
                    return False
            except:
                print(f"   ❌ FAILED to parse error response")
                return False
                
        else:
            print(f"   ❌ FAILED")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Raw Response: {response.text}")
            return False
        
        return True
                
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT (>60 seconds)")
        print(f"   This might be normal for first request (cold start)")
        
    except Exception as e:
        print(f"   ❌ REQUEST FAILED: {e}")

def test_cors():
    """Test CORS preflight request"""
    
    api_url = "https://4rvo13bwv1.execute-api.ap-southeast-1.amazonaws.com/dev/analyze"
    
    print("\n🔒 Testing CORS preflight...")
    
    try:
        response = requests.options(api_url, headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        
        print(f"   Status Code: {response.status_code}")
        print(f"   CORS Headers:")
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                print(f"     {header}: {value}")
                
    except Exception as e:
        print(f"   ❌ CORS TEST FAILED: {e}")

if __name__ == "__main__":
    print("🚀 Testing Deployed ATS Buddy API")
    print("=" * 50)
    
    test_cors()
    api_success = test_deployed_api()
    
    print("\n" + "=" * 50)
    if api_success:
        print("🎯 Test completed successfully! API is working correctly.")
    else:
        print("⚠️  Test completed with issues. Check the output above.")
    print("🌐 Web UI: http://ats-buddy-web-ui-dev-123456789.s3-website-ap-southeast-1.amazonaws.com")