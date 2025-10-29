#!/usr/bin/env python3
"""
Quick test script for ATS Buddy - Windows friendly
Tests the Lambda handler with sample data
"""

import sys
import json
import os

# Add src directory to path
sys.path.append('src')

def test_bedrock_only():
    """Test just the Bedrock AI analysis without S3 reports"""
    print("🤖 Testing Bedrock AI Analysis Only")
    print("=" * 40)
    
    try:
        from bedrock_client import BedrockClient
        
        client = BedrockClient()
        print(f"✅ Bedrock client initialized: {client.model_id}")
        
        # Sample data
        resume_text = '''
        John Doe - Software Engineer
        
        SKILLS:
        • Python, JavaScript, HTML, CSS
        • MySQL, PostgreSQL
        • Git, GitHub
        • Linux, Windows
        
        EXPERIENCE:
        Software Developer (2021-2024)
        • Built web applications using Python and Flask
        • Worked with MySQL databases
        • Collaborated with teams using Git
        '''
        
        job_description = '''
        Senior Software Engineer Position
        
        Requirements:
        • 5+ years Python experience
        • AWS cloud services knowledge
        • Docker containerization
        • Kubernetes orchestration
        • CI/CD pipeline experience
        • Strong communication skills
        
        Preferred:
        • React/JavaScript frontend
        • PostgreSQL database
        • Microservices architecture
        '''
        
        print("🔍 Running AI analysis...")
        result = client.analyze_resume_vs_job_description(resume_text, job_description)
        
        if result['success']:
            analysis = result['analysis']
            print("✅ SUCCESS!")
            print(f"🎯 Compatibility Score: {analysis['compatibility_score']}%")
            print(f"🔍 Missing Keywords: {len(analysis['missing_keywords'])}")
            print(f"💡 Suggestions: {len(analysis['suggestions'])}")
            
            print(f"\n📋 Top Missing Keywords:")
            for keyword in analysis['missing_keywords'][:5]:
                print(f"   • {keyword}")
                
            print(f"\n💡 Top Suggestions:")
            for i, suggestion in enumerate(analysis['suggestions'][:3], 1):
                print(f"   {i}. {suggestion}")
                
        else:
            print(f"❌ Analysis failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_handler():
    """Test the Lambda handler with sample data"""
    print("🧪 ATS Buddy Quick Test")
    print("=" * 40)
    
    try:
        from handler import lambda_handler
        
        # Sample event
        event = {
            'resume_text': '''
            John Doe - Software Engineer
            
            SKILLS:
            • Python, JavaScript, HTML, CSS
            • MySQL, PostgreSQL
            • Git, GitHub
            • Linux, Windows
            
            EXPERIENCE:
            Software Developer (2021-2024)
            • Built web applications using Python and Flask
            • Worked with MySQL databases
            • Collaborated with teams using Git
            ''',
            'job_description': '''
            Senior Software Engineer Position
            
            Requirements:
            • 5+ years Python experience
            • AWS cloud services knowledge
            • Docker containerization
            • Kubernetes orchestration
            • CI/CD pipeline experience
            • Strong communication skills
            
            Preferred:
            • React/JavaScript frontend
            • PostgreSQL database
            • Microservices architecture
            ''',
            'job_title': 'Senior Software Engineer'
        }
        
        print("📝 Testing with sample resume and job description...")
        print(f"   Resume length: {len(event['resume_text'])} characters")
        print(f"   Job description length: {len(event['job_description'])} characters")
        
        # Call the handler
        print("\n🚀 Calling Lambda handler...")
        result = lambda_handler(event, {})
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Status Code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            # Parse body (handle both string and dict)
            body = result['body'] if isinstance(result['body'], dict) else json.loads(result['body'])
            
            if body['success']:
                print("   ✅ SUCCESS!")
                analysis = body['analysis_summary']
                print(f"   🎯 Compatibility Score: {analysis['compatibility_score']}%")
                print(f"   🔍 Missing Keywords: {analysis['missing_keywords_count']}")
                print(f"   💡 Suggestions: {analysis['suggestions_count']}")
                
                # Show reports info if available
                if 'reports' in body:
                    print(f"   📋 Report ID: {body['reports']['report_id']}")
                    print("   📄 Reports generated: Markdown & HTML")
                
            else:
                print("   ❌ Analysis failed")
                print(f"   Error: {body.get('error', 'Unknown error')}")
                
        else:
            # Handle error response
            body = result['body'] if isinstance(result['body'], dict) else json.loads(result['body'])
            print("   ❌ FAILED")
            error_msg = body.get('error', 'Unknown error')
            print(f"   Error: {error_msg}")
            
            # Specific troubleshooting based on error
            print("\n🔧 Troubleshooting:")
            if "S3" in error_msg or "bucket" in error_msg.lower():
                print("   • S3 bucket not configured - Deploy infrastructure first:")
                print("     cd infra && sam build && sam deploy --guided")
                print("   • Or set environment variables manually:")
                print("     set REPORTS_BUCKET=your-bucket-name (Windows)")
                print("     export REPORTS_BUCKET=your-bucket-name (Mac/Linux)")
            else:
                print("   • Check AWS credentials are configured")
                print("   • Ensure Bedrock access is enabled in your AWS account")
                print("   • Verify Nova Pro model access in Bedrock console")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the ats-buddy directory")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check the error details above")

if __name__ == "__main__":
    print("🧪 ATS Buddy Quick Test")
    print("=" * 50)
    print("Choose test mode:")
    print("1. 🤖 Bedrock AI Analysis Only (Recommended)")
    print("2. 🚀 Full Lambda Handler (Requires S3 setup)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_bedrock_only()
    elif choice == "2":
        test_handler()
    else:
        print("Invalid choice. Running Bedrock-only test...")
        test_bedrock_only()
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\n💡 Next steps:")
    print("   • If successful: Try with your own resume text")
    print("   • If failed: Check AWS credentials and Bedrock access")
    print("   • For full deployment: See infra/DEPLOYMENT_GUIDE.md")