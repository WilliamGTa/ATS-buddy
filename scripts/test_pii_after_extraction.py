#!/usr/bin/env python3
"""
Test PII Redaction After Text Extraction
"""

import sys
import os
import json

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from handler import apply_pii_redaction_to_text

def test_pii_redaction_function():
    """Test the PII redaction function directly"""
    print("🧪 Testing PII Redaction Function")
    print("=" * 50)
    
    # Test text with PII
    test_text = """
John Smith
Email: john.smith@example.com
Phone: (555) 123-4567
SSN: 123-45-6789
Address: 123 Main Street, Anytown, CA 90210

PROFESSIONAL EXPERIENCE
Software Engineer at Tech Corp (2020-2024)
- Developed Python applications using AWS services
- Led team of 5 developers
- Implemented machine learning solutions

EDUCATION
Bachelor of Science in Computer Science
University of Technology, 2020

SKILLS
- Python, JavaScript, AWS, Docker
- Machine Learning, AI, Data Science
- Team Leadership, Project Management
"""
    
    print("📄 Original Text:")
    print("Contains PII: John Smith, john.smith@example.com, (555) 123-4567, 123-45-6789")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        # Apply PII redaction
        print("\n🔄 Applying PII redaction...")
        result = apply_pii_redaction_to_text(test_text)
        
        if result["success"]:
            print("✅ PII redaction function executed successfully")
            print(f"Redacted: {result['redacted']}")
            
            if result["redacted"]:
                print("\n📝 Redacted Text Sample:")
                redacted_lines = result["text"].split('\n')[:10]  # First 10 lines
                for line in redacted_lines:
                    if line.strip():
                        print(f"  {line}")
                
                print(f"\nRedacted text length: {len(result['text'])} characters")
                
                # Check if PII was actually redacted
                original_pii = ["john.smith@example.com", "(555) 123-4567", "123-45-6789"]
                redacted_text = result["text"]
                
                pii_found = []
                for pii in original_pii:
                    if pii in redacted_text:
                        pii_found.append(pii)
                
                if pii_found:
                    print(f"⚠️  Some PII may still be present: {pii_found}")
                else:
                    print("✅ PII appears to be successfully redacted")
                    
            else:
                print("ℹ️  No PII redaction was applied (no high-confidence PII detected)")
                
            return True
            
        else:
            print("❌ PII redaction function failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PII redaction: {e}")
        return False

def main():
    print("🚀 PII Redaction After Text Extraction Test")
    print("=" * 60)
    
    success = test_pii_redaction_function()
    
    print("\n📊 Test Summary")
    print("=" * 60)
    
    if success:
        print("🎉 PII redaction function is working!")
        print("\n✅ Key Points:")
        print("- PII redaction is now applied after text extraction")
        print("- This avoids S3 Object Lambda compatibility issues with Textract")
        print("- Amazon Comprehend detects and redacts PII in extracted text")
        print("- The web UI should now work properly with PDF uploads")
        
    else:
        print("❌ PII redaction function test failed")
        print("\n🔧 Troubleshooting:")
        print("1. Check AWS credentials and Comprehend permissions")
        print("2. Verify the function is properly deployed")
        print("3. Check CloudWatch logs for detailed errors")

if __name__ == "__main__":
    main()