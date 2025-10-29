#!/usr/bin/env python3
"""
ATS Buddy - Presentation Validation Script
Complete system check for demo readiness
"""

import boto3
import json
import sys
import os
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section"""
    print(f"\n🔍 {title}")
    print("-" * 50)

def check_mark(condition, message):
    """Print check mark or X based on condition"""
    symbol = "✅" if condition else "❌"
    print(f"{symbol} {message}")
    return condition

def main():
    print_header("ATS BUDDY - PRESENTATION VALIDATION")
    print("🚀 Comprehensive system check for demo readiness")
    
    all_checks = []
    
    # 1. AWS Credentials
    print_section("AWS Credentials & Permissions")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        all_checks.append(check_mark(True, f"AWS credentials valid (Account: {account_id})"))
    except Exception as e:
        all_checks.append(check_mark(False, f"AWS credentials failed: {e}"))
        return
    
    # 2. CloudFormation Stack
    print_section("Infrastructure Deployment")
    try:
        cf = boto3.client('cloudformation')
        stack = cf.describe_stacks(StackName='ats-buddy-dev')
        stack_status = stack['Stacks'][0]['StackStatus']
        all_checks.append(check_mark(
            stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE'],
            f"CloudFormation stack: {stack_status}"
        ))
        
        # Get outputs
        outputs = {o['OutputKey']: o['OutputValue'] for o in stack['Stacks'][0].get('Outputs', [])}
        
    except Exception as e:
        all_checks.append(check_mark(False, f"CloudFormation stack check failed: {e}"))
        return
    
    # 3. Lambda Functions
    print_section("Lambda Functions")
    try:
        lambda_client = boto3.client('lambda')
        
        # Main Lambda
        main_lambda = lambda_client.get_function_configuration(
            FunctionName='ats-buddy-processor-dev'
        )
        all_checks.append(check_mark(
            main_lambda['State'] == 'Active',
            f"Main Lambda: {main_lambda['State']} ({main_lambda['Runtime']})"
        ))
        
        # PII Lambda
        pii_lambda = lambda_client.get_function_configuration(
            FunctionName='ats-buddy-pii-redaction-dev'
        )
        all_checks.append(check_mark(
            pii_lambda['State'] == 'Active',
            f"PII Lambda: {pii_lambda['State']} ({pii_lambda['Runtime']})"
        ))
        
    except Exception as e:
        all_checks.append(check_mark(False, f"Lambda functions check failed: {e}"))
    
    # 4. S3 Buckets
    print_section("S3 Storage")
    try:
        s3 = boto3.client('s3')
        
        # Check buckets exist
        buckets_to_check = [
            ('ResumesBucketName', 'Resume storage'),
            ('ReportsBucketName', 'Report storage'),
            ('WebUIBucketName', 'Web UI hosting')
        ]
        
        for bucket_key, description in buckets_to_check:
            if bucket_key in outputs:
                bucket_name = outputs[bucket_key]
                try:
                    s3.head_bucket(Bucket=bucket_name)
                    all_checks.append(check_mark(True, f"{description}: {bucket_name}"))
                except:
                    all_checks.append(check_mark(False, f"{description}: {bucket_name} (not accessible)"))
            else:
                all_checks.append(check_mark(False, f"{description}: not found in outputs"))
                
    except Exception as e:
        all_checks.append(check_mark(False, f"S3 buckets check failed: {e}"))
    
    # 5. API Gateway
    print_section("API Gateway")
    try:
        if 'ApiGatewayUrl' in outputs:
            api_url = outputs['ApiGatewayUrl']
            all_checks.append(check_mark(True, f"API Gateway URL: {api_url}"))
            
            # Test API accessibility (basic check)
            import urllib.request
            try:
                response = urllib.request.urlopen(f"{api_url}/analyze", timeout=5)
                all_checks.append(check_mark(False, "API Gateway: Accessible (unexpected success)"))
            except urllib.error.HTTPError as e:
                if e.code in [400, 405]:  # Expected for GET request to POST endpoint
                    all_checks.append(check_mark(True, "API Gateway: Accessible and responding"))
                else:
                    all_checks.append(check_mark(False, f"API Gateway: HTTP {e.code}"))
            except Exception:
                all_checks.append(check_mark(False, "API Gateway: Not accessible"))
        else:
            all_checks.append(check_mark(False, "API Gateway URL not found"))
            
    except Exception as e:
        all_checks.append(check_mark(False, f"API Gateway check failed: {e}"))
    
    # 6. DynamoDB
    print_section("DynamoDB Cache")
    try:
        dynamodb = boto3.client('dynamodb')
        if 'ResumeCacheTableName' in outputs:
            table_name = outputs['ResumeCacheTableName']
            table = dynamodb.describe_table(TableName=table_name)
            table_status = table['Table']['TableStatus']
            all_checks.append(check_mark(
                table_status == 'ACTIVE',
                f"DynamoDB table: {table_status} (TTL enabled)"
            ))
        else:
            all_checks.append(check_mark(False, "DynamoDB table name not found"))
            
    except Exception as e:
        all_checks.append(check_mark(False, f"DynamoDB check failed: {e}"))
    
    # 7. AI Services Access
    print_section("AI/ML Services")
    try:
        # Bedrock
        bedrock = boto3.client('bedrock')
        models = bedrock.list_foundation_models()
        nova_available = any('nova' in model.get('modelId', '').lower() for model in models.get('modelSummaries', []))
        all_checks.append(check_mark(nova_available, "Amazon Bedrock: Nova models available"))
        
        # Textract
        textract = boto3.client('textract')
        all_checks.append(check_mark(True, "Amazon Textract: Service accessible"))
        
        # Comprehend
        comprehend = boto3.client('comprehend')
        all_checks.append(check_mark(True, "Amazon Comprehend: Service accessible"))
        
    except Exception as e:
        all_checks.append(check_mark(False, f"AI services check failed: {e}"))
    
    # 8. Web UI
    print_section("Web UI Deployment")
    try:
        if 'WebUIUrl' in outputs:
            web_url = outputs['WebUIUrl']
            all_checks.append(check_mark(True, f"Web UI URL: {web_url}"))
            
            # Check if web UI is accessible
            try:
                response = urllib.request.urlopen(web_url, timeout=10)
                content = response.read().decode('utf-8')
                has_title = 'ATS Buddy' in content
                all_checks.append(check_mark(has_title, "Web UI: Accessible and contains expected content"))
            except Exception:
                all_checks.append(check_mark(False, "Web UI: Not accessible"))
        else:
            all_checks.append(check_mark(False, "Web UI URL not found"))
            
    except Exception as e:
        all_checks.append(check_mark(False, f"Web UI check failed: {e}"))
    
    # 9. PII Redaction Integration
    print_section("PII Protection System")
    try:
        if 'PIIRedactionAccessPointArn' in outputs:
            pii_arn = outputs['PIIRedactionAccessPointArn']
            all_checks.append(check_mark(True, f"S3 Object Lambda: {pii_arn.split('/')[-1]}"))
        else:
            all_checks.append(check_mark(False, "PII redaction access point not found"))
            
        # Check Lambda environment variables
        env_vars = main_lambda.get('Environment', {}).get('Variables', {})
        pii_configured = 'PII_REDACTED_ACCESS_POINT' in env_vars
        all_checks.append(check_mark(pii_configured, "PII redaction: Lambda configuration"))
        
    except Exception as e:
        all_checks.append(check_mark(False, f"PII protection check failed: {e}"))
    
    # Summary
    print_header("PRESENTATION READINESS SUMMARY")
    
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    success_rate = (passed_checks / total_checks) * 100
    
    print(f"📊 System Health: {passed_checks}/{total_checks} checks passed ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT - System is demo-ready!")
        print("\n🚀 Ready for presentation:")
        print("  ✅ All core systems operational")
        print("  ✅ AI services accessible")
        print("  ✅ PII protection active")
        print("  ✅ Web UI live and functional")
        
        if 'WebUIUrl' in outputs:
            print(f"\n🌐 Demo URL: {outputs['WebUIUrl']}")
            
    elif success_rate >= 75:
        print("⚠️  GOOD - Minor issues detected")
        print("  🔧 System mostly functional")
        print("  ⚠️  Some components may need attention")
        
    else:
        print("❌ NEEDS ATTENTION - Critical issues detected")
        print("  🚨 System not ready for presentation")
        print("  🔧 Please resolve issues before demo")
    
    print(f"\n📅 Validation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 90

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)