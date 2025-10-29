#!/usr/bin/env python3
"""
End-to-End Test
Tests the complete ATS Buddy workflow
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set minimal environment variables for testing
os.environ.setdefault('RESUME_CACHE_TABLE', 'test-cache-table')
os.environ.setdefault('REPORTS_BUCKET', 'test-reports-bucket')
os.environ.setdefault('RESUMES_BUCKET', 'test-resumes-bucket')

from handler import lambda_handler

def test_complete_workflow():
    """Test the complete workflow with sample data"""
    
    # Sample data for testing
    sample_resume = """
    John Doe
    Software Engineer
    
    Experience:
    - 5 years Python development
    - AWS cloud services experience
    - Docker and Kubernetes
    - CI/CD pipeline implementation
    
    Education:
    Bachelor of Computer Science
    """
    
    sample_job_description = """
    Senior Software Engineer with expertise in Python, AWS, and machine learning.
    Experience with Django, Flask, TensorFlow, PyTorch, RESTful APIs, microservices,
    Docker, Kubernetes, CI/CD pipelines, and engineering management required.
    """
    
    # Test event
    event = {
        'resume_text': sample_resume,
        'job_description': sample_job_description,
        'job_title': 'Senior Software Engineer'
    }
    
    # Execute handler
    result = lambda_handler(event, None)
    
    # Validate response
    assert result['statusCode'] == 200
    
    # Parse response body
    import json
    body = result['body'] if isinstance(result['body'], dict) else json.loads(result['body'])
    
    # Validate response structure
    assert body['success'] == True
    assert 'analysis_summary' in body
    assert 'compatibility_score' in body['analysis_summary']
    
    print(f"✅ Test passed - Compatibility Score: {body['analysis_summary']['compatibility_score']}%")

def run_manual_test():
    """Function to run the test manually outside pytest"""
    try:
        test_complete_workflow()
        print("🎉 End-to-end test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = run_manual_test()
    sys.exit(0 if success else 1)