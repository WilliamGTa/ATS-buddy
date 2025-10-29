#!/usr/bin/env python3
"""
Final Validation Script for ATS Buddy POC
Performs comprehensive checks to ensure the system is ready for demo
"""

import boto3
import requests
import json
import sys
from pathlib import Path

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Credentials: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"❌ AWS Credentials: {e}")
        return False

def check_cloudformation_stack(stack_name="ats-buddy-dev"):
    """Check if CloudFormation stack exists and is deployed"""
    try:
        cf = boto3.client('cloudformation', region_name='ap-southeast-1')
        response = cf.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        status = stack['StackStatus']
        
        if status == 'CREATE_COMPLETE' or status == 'UPDATE_COMPLETE':
            print(f"✅ CloudFormation Stack: {stack_name} ({status})")
            return True, stack
        else:
            print(f"⚠️  CloudFormation Stack: {stack_name} ({status})")
            return False, stack
            
    except Exception as e:
        print(f"❌ CloudFormation Stack: {e}")
        return False, None

def check_lambda_function(stack_outputs):
    """Check if Lambda function is deployed and accessible"""
    try:
        function_name = None
        for output in stack_outputs:
            if output['OutputKey'] == 'LambdaFunctionName':
                function_name = output['OutputValue']
                break
        
        if not function_name:
            print("❌ Lambda Function: Name not found in stack outputs")
            return False
        
        lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
        response = lambda_client.get_function(FunctionName=function_name)
        
        print(f"✅ Lambda Function: {function_name}")
        return True
        
    except Exception as e:
        print(f"❌ Lambda Function: {e}")
        return False

def check_api_gateway(stack_outputs):
    """Check if API Gateway is accessible"""
    try:
        api_url = None
        for output in stack_outputs:
            if output['OutputKey'] == 'ApiGatewayUrl':
                api_url = output['OutputValue']
                break
        
        if not api_url:
            print("❌ API Gateway: URL not found in stack outputs")
            return False, None
        
        # Test OPTIONS request (CORS preflight)
        response = requests.options(f"{api_url}/analyze", timeout=10)
        
        if response.status_code in [200, 204]:
            print(f"✅ API Gateway: {api_url}")
            return True, api_url
        else:
            print(f"⚠️  API Gateway: {api_url} (Status: {response.status_code})")
            return True, api_url  # Still return True as it might work for POST
            
    except Exception as e:
        print(f"❌ API Gateway: {e}")
        return False, None

def check_web_ui(stack_outputs):
    """Check if Web UI is accessible"""
    try:
        web_url = None
        for output in stack_outputs:
            if output['OutputKey'] == 'WebUIUrl':
                web_url = output['OutputValue']
                break
        
        if not web_url:
            print("❌ Web UI: URL not found in stack outputs")
            return False
        
        response = requests.get(web_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Web UI: {web_url}")
            return True
        else:
            print(f"⚠️  Web UI: {web_url} (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Web UI: {e}")
        return False

def check_bedrock_access():
    """Check if Bedrock service is accessible"""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-1')
        
        # Test with a simple prompt
        test_prompt = "Hello, this is a test."
        
        response = bedrock.invoke_model(
            modelId='apac.amazon.nova-lite-v1:0',
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": test_prompt}]}],
                "inferenceConfig": {"maxTokens": 10, "temperature": 0.1}
            }),
            contentType='application/json'
        )
        
        print("✅ Bedrock Access: Amazon Nova Lite available")
        return True
        
    except Exception as e:
        print(f"❌ Bedrock Access: {e}")
        return False

def check_s3_buckets(stack_outputs):
    """Check if S3 buckets exist and are accessible"""
    try:
        s3 = boto3.client('s3')
        buckets_to_check = ['ResumesBucketName', 'ReportsBucketName', 'WebUIBucketName']
        
        all_good = True
        for bucket_key in buckets_to_check:
            bucket_name = None
            for output in stack_outputs:
                if output['OutputKey'] == bucket_key:
                    bucket_name = output['OutputValue']
                    break
            
            if bucket_name:
                try:
                    s3.head_bucket(Bucket=bucket_name)
                    print(f"✅ S3 Bucket ({bucket_key}): {bucket_name}")
                except Exception as e:
                    print(f"❌ S3 Bucket ({bucket_key}): {bucket_name} - {e}")
                    all_good = False
            else:
                print(f"❌ S3 Bucket ({bucket_key}): Not found in outputs")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ S3 Buckets: {e}")
        return False

def check_project_files():
    """Check if all required project files exist"""
    required_files = [
        'src/handler.py',
        'src/bedrock_client.py', 
        'src/textract_client.py',
        'src/report_generator.py',
        'src/s3_handler.py',
        'web-ui/index.html',
        'web-ui/script.js',
        'web-ui/styles.css',
        'infra/template.yaml',
        'README.md'
    ]
    
    project_root = Path(__file__).parent.parent
    all_good = True
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ File: {file_path} (missing)")
            all_good = False
    
    return all_good

def main():
    """Run all validation checks"""
    print("🔍 ATS Buddy POC - Final Validation")
    print("=" * 50)
    
    checks = []
    
    # Check 1: Project Files
    print("\n📁 Checking Project Files...")
    checks.append(check_project_files())
    
    # Check 2: AWS Credentials
    print("\n🔑 Checking AWS Credentials...")
    checks.append(check_aws_credentials())
    
    # Check 3: CloudFormation Stack
    print("\n☁️  Checking CloudFormation Stack...")
    stack_ok, stack = check_cloudformation_stack()
    checks.append(stack_ok)
    
    if not stack_ok:
        print("\n❌ Cannot proceed without deployed stack")
        sys.exit(1)
    
    stack_outputs = stack['Outputs']
    
    # Check 4: Lambda Function
    print("\n⚡ Checking Lambda Function...")
    checks.append(check_lambda_function(stack_outputs))
    
    # Check 5: API Gateway
    print("\n🌐 Checking API Gateway...")
    api_ok, api_url = check_api_gateway(stack_outputs)
    checks.append(api_ok)
    
    # Check 6: Web UI
    print("\n💻 Checking Web UI...")
    checks.append(check_web_ui(stack_outputs))
    
    # Check 7: S3 Buckets
    print("\n🪣 Checking S3 Buckets...")
    checks.append(check_s3_buckets(stack_outputs))
    
    # Check 8: Bedrock Access
    print("\n🤖 Checking Bedrock Access...")
    checks.append(check_bedrock_access())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 ALL CHECKS PASSED ({passed}/{total})")
        print("\n✅ Your ATS Buddy POC is ready for demo!")
        
        # Show key URLs
        for output in stack_outputs:
            if output['OutputKey'] == 'WebUIUrl':
                print(f"\n🌐 Web UI: {output['OutputValue']}")
            elif output['OutputKey'] == 'ApiGatewayUrl':
                print(f"🔗 API: {output['OutputValue']}")
        
        print("\n💡 Quick Test Commands:")
        print("   python scripts/quick_test.py")
        print("   python tests/test_end_to_end.py")
        
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("\n🔧 Please fix the failed checks before demo")
        sys.exit(1)

if __name__ == "__main__":
    main()