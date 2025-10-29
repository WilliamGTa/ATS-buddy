#!/usr/bin/env python3
"""
Helper script to get S3 bucket names after deployment
"""

import boto3
import sys

def get_bucket_names(stack_name="ats-buddy-dev"):
    """Get bucket names from CloudFormation stack outputs"""
    try:
        cf = boto3.client('cloudformation')
        
        print(f"🔍 Getting bucket names from stack: {stack_name}")
        
        response = cf.describe_stacks(StackName=stack_name)
        outputs = response['Stacks'][0]['Outputs']
        
        resumes_bucket = None
        reports_bucket = None
        
        for output in outputs:
            if output['OutputKey'] == 'ResumesBucketName':
                resumes_bucket = output['OutputValue']
            elif output['OutputKey'] == 'ReportsBucketName':
                reports_bucket = output['OutputValue']
        
        if resumes_bucket and reports_bucket:
            print("✅ Found bucket names!")
            print(f"\n📁 Resumes Bucket: {resumes_bucket}")
            print(f"📁 Reports Bucket: {reports_bucket}")
            
            print(f"\n💡 To set environment variables:")
            print(f"Windows:")
            print(f"  set RESUMES_BUCKET={resumes_bucket}")
            print(f"  set REPORTS_BUCKET={reports_bucket}")
            
            print(f"\nMac/Linux:")
            print(f"  export RESUMES_BUCKET={resumes_bucket}")
            print(f"  export REPORTS_BUCKET={reports_bucket}")
            
            print(f"\n🧪 Then test with:")
            print(f"  python quick_test.py")
            
        else:
            print("❌ Could not find bucket names in stack outputs")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n💡 Make sure:")
        print(f"  • AWS credentials are configured")
        print(f"  • Stack '{stack_name}' exists")
        print(f"  • You have CloudFormation read permissions")

if __name__ == "__main__":
    stack_name = sys.argv[1] if len(sys.argv) > 1 else "ats-buddy-dev"
    get_bucket_names(stack_name)