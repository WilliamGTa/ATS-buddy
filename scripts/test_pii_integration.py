#!/usr/bin/env python3
"""
Test PII Redaction Integration with Deployed Lambda
"""

import json
import boto3
import sys
import os

def test_lambda_pii_configuration():
    """Test if the deployed Lambda has PII redaction configured"""
    print("🔍 Testing Deployed Lambda PII Configuration")
    print("=" * 50)
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Get Lambda function configuration
        response = lambda_client.get_function_configuration(
            FunctionName='ats-buddy-processor-dev'
        )
        
        env_vars = response.get('Environment', {}).get('Variables', {})
        pii_access_point = env_vars.get('PII_REDACTED_ACCESS_POINT')
        
        print(f"Lambda Function: {response['FunctionName']}")
        print(f"Runtime: {response['Runtime']}")
        print(f"PII Access Point: {pii_access_point}")
        
        if pii_access_point:
            print("✅ PII redaction access point is configured in Lambda")
            return True, pii_access_point
        else:
            print("❌ PII redaction access point not found in Lambda environment")
            return False, None
            
    except Exception as e:
        print(f"❌ Error checking Lambda configuration: {e}")
        return False, None

def test_s3_object_lambda_access_point(access_point_arn):
    """Test if the S3 Object Lambda access point exists and is accessible"""
    print("\n🔍 Testing S3 Object Lambda Access Point")
    print("=" * 50)
    
    try:
        s3control = boto3.client('s3control')
        
        # Extract access point name from ARN
        # ARN format: arn:aws:s3-object-lambda:region:account:accesspoint/name
        access_point_name = access_point_arn.split('/')[-1]
        account_id = access_point_arn.split(':')[4]
        
        # Get access point configuration
        response = s3control.get_access_point_configuration_for_object_lambda(
            AccountId=account_id,
            Name=access_point_name
        )
        
        print(f"Access Point Name: {access_point_name}")
        print(f"Supporting Access Point: {response['Configuration']['SupportingAccessPoint']}")
        
        transformations = response['Configuration']['TransformationConfigurations']
        for i, transform in enumerate(transformations):
            print(f"Transformation {i+1}:")
            print(f"  Actions: {transform['Actions']}")
            print(f"  Lambda ARN: {transform['ContentTransformation']['AwsLambda']['FunctionArn']}")
        
        print("✅ S3 Object Lambda access point is properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error checking S3 Object Lambda access point: {e}")
        return False

def test_pii_redaction_lambda():
    """Test if the PII redaction Lambda function exists"""
    print("\n🔍 Testing PII Redaction Lambda Function")
    print("=" * 50)
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Get PII redaction Lambda function
        response = lambda_client.get_function_configuration(
            FunctionName='ats-buddy-pii-redaction-dev'
        )
        
        print(f"Function Name: {response['FunctionName']}")
        print(f"Runtime: {response['Runtime']}")
        print(f"Handler: {response['Handler']}")
        print(f"Timeout: {response['Timeout']} seconds")
        print(f"Memory: {response['MemorySize']} MB")
        
        print("✅ PII redaction Lambda function is deployed and configured")
        return True
        
    except Exception as e:
        print(f"❌ Error checking PII redaction Lambda: {e}")
        return False

def create_test_file_with_pii():
    """Create a test text file with PII for testing"""
    print("\n📄 Creating Test File with PII")
    print("=" * 50)
    
    test_content = """
John Smith
Email: john.smith@example.com
Phone: (555) 123-4567
SSN: 123-45-6789
Address: 123 Main Street, Anytown, CA 90210

This is a test document containing personally identifiable information.
The person's credit card number is 4532-1234-5678-9012.
Their date of birth is 01/15/1985.
"""
    
    try:
        s3 = boto3.client('s3')
        bucket_name = 'ats-buddy-dev-resumesbucket-e1fjwrzodx0s'  # From deployment output
        test_key = 'test-pii-document.txt'
        
        # Upload test file
        s3.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        print(f"✅ Test file uploaded: s3://{bucket_name}/{test_key}")
        print("File contains PII: Name, Email, Phone, SSN, Address, Credit Card")
        
        return bucket_name, test_key
        
    except Exception as e:
        print(f"❌ Error creating test file: {e}")
        return None, None

def main():
    print("🧪 ATS Buddy PII Redaction Integration Test")
    print("=" * 60)
    
    # Test 1: Lambda Configuration
    lambda_ok, access_point_arn = test_lambda_pii_configuration()
    
    # Test 2: S3 Object Lambda Access Point
    s3_ok = False
    if access_point_arn:
        s3_ok = test_s3_object_lambda_access_point(access_point_arn)
    
    # Test 3: PII Redaction Lambda
    pii_lambda_ok = test_pii_redaction_lambda()
    
    # Test 4: Create test file (optional)
    bucket_name, test_key = create_test_file_with_pii()
    
    # Summary
    print("\n📊 Integration Test Results")
    print("=" * 60)
    
    total_tests = 3
    passed_tests = sum([lambda_ok, s3_ok, pii_lambda_ok])
    
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All integration tests passed!")
        print("\n✅ PII Redaction is fully configured and ready")
        
        if bucket_name and test_key:
            print(f"\n🔧 Next Steps:")
            print(f"1. Test with the uploaded file: s3://{bucket_name}/{test_key}")
            print(f"2. Run ATS Buddy analysis on a resume with PII")
            print(f"3. Verify PII is redacted in the extracted text")
        
    else:
        print("❌ Some integration tests failed")
        print("\n🔧 Issues to resolve:")
        if not lambda_ok:
            print("- Lambda function PII configuration")
        if not s3_ok:
            print("- S3 Object Lambda access point")
        if not pii_lambda_ok:
            print("- PII redaction Lambda function")

if __name__ == "__main__":
    main()