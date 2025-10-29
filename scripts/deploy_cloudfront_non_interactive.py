#!/usr/bin/env python3
"""
Deploy ATS Buddy with CloudFront Distribution (Non-Interactive)
Complete deployment script that doesn't require user input
"""

import boto3
import subprocess
import sys
import time
import json
from pathlib import Path

def run_command(command, cwd=None, interactive=False):
    """Run shell command and return success status"""
    try:
        print(f"🔧 Running: {command}")
        
        if interactive:
            # For interactive commands, don't capture output
            result = subprocess.run(command, shell=True, cwd=cwd)
            return result.returncode == 0
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Command completed successfully")
                if result.stdout.strip():
                    print(result.stdout)
                return True
            else:
                print(f"❌ Command failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
            
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check AWS CLI
    if not run_command("aws --version"):
        print("❌ AWS CLI not found. Please install AWS CLI and configure credentials.")
        return False
    
    # Check SAM CLI
    if not run_command("sam --version"):
        print("❌ SAM CLI not found. Please install SAM CLI.")
        return False
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        return False
    
    return True

def check_existing_stack():
    """Check if stack already exists"""
    try:
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='ats-buddy-dev')
        print("✅ Found existing stack: ats-buddy-dev")
        return True
    except cf.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            print("ℹ️  Stack ats-buddy-dev does not exist, will create new")
            return False
        else:
            print(f"❌ Error checking stack: {e}")
            return None

def deploy_infrastructure():
    """Deploy the SAM infrastructure with CloudFront"""
    print("\n🏗️  Deploying infrastructure with CloudFront...")
    
    infra_dir = Path(__file__).parent.parent / 'infra'
    
    # Build SAM application
    print("\n📦 Building SAM application...")
    if not run_command("sam build", cwd=infra_dir):
        return False
    
    # Check if stack exists
    stack_exists = check_existing_stack()
    if stack_exists is None:
        return False
    
    # Deploy based on whether stack exists
    if stack_exists:
        print("\n🔄 Updating existing stack...")
        deploy_cmd = "sam deploy --no-confirm-changeset --no-fail-on-empty-changeset"
    else:
        print("\n🆕 Creating new stack with default parameters...")
        deploy_cmd = (
            "sam deploy "
            "--stack-name ats-buddy-dev "
            "--capabilities CAPABILITY_NAMED_IAM "
            "--region ap-southeast-1 "
            "--no-confirm-changeset "
            "--no-fail-on-empty-changeset "
            "--parameter-overrides Environment=dev BedrockRegion=ap-southeast-1"
        )
    
    if not run_command(deploy_cmd, cwd=infra_dir):
        return False
    
    return True

def get_deployment_outputs():
    """Get deployment outputs from CloudFormation"""
    try:
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='ats-buddy-dev')
        
        outputs = {}
        for output in response['Stacks'][0]['Outputs']:
            outputs[output['OutputKey']] = output['OutputValue']
        
        return outputs
        
    except Exception as e:
        print(f"❌ Error getting deployment outputs: {e}")
        return None

def deploy_web_ui():
    """Deploy web UI files to S3 and CloudFront"""
    print("\n🌐 Deploying Web UI to CloudFront...")
    
    script_path = Path(__file__).parent / 'deploy_web_ui.py'
    
    if not run_command(f"python {script_path}"):
        return False
    
    return True

def display_deployment_summary(outputs):
    """Display deployment summary with security highlights"""
    print("\n" + "="*60)
    print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    print("\n🔗 Access URLs:")
    if 'WebUIUrl' in outputs:
        print(f"   🌐 Web UI (CloudFront): {outputs['WebUIUrl']}")
    if 'ApiGatewayUrl' in outputs:
        print(f"   🚪 API Gateway: {outputs['ApiGatewayUrl']}")
    
    print("\n🔒 Security Features:")
    print("   ✅ No AWS account ID exposed in URLs")
    print("   ✅ HTTPS encryption enforced")
    print("   ✅ Private S3 buckets (CloudFront access only)")
    print("   ✅ PII redaction with Amazon Comprehend")
    print("   ✅ Global CDN for performance and security")
    
    print("\n📊 AWS Resources Created:")
    if 'WebUIBucketName' in outputs:
        print(f"   📁 Web UI S3 Bucket: {outputs['WebUIBucketName']}")
    if 'CloudFrontDistributionId' in outputs:
        print(f"   🌐 CloudFront Distribution: {outputs['CloudFrontDistributionId']}")
    if 'ResumesBucketName' in outputs:
        print(f"   📄 Resumes S3 Bucket: {outputs['ResumesBucketName']}")
    if 'ReportsBucketName' in outputs:
        print(f"   📊 Reports S3 Bucket: {outputs['ReportsBucketName']}")
    if 'LambdaFunctionName' in outputs:
        print(f"   ⚡ Lambda Function: {outputs['LambdaFunctionName']}")
    
    print("\n💡 Next Steps:")
    print("   1. Access the Web UI using the CloudFront URL above")
    print("   2. Upload a PDF resume and job description to test")
    print("   3. Run validation: python scripts/final_validation.py")
    
    print("\n🔄 To update Web UI files:")
    print("   python scripts/deploy_web_ui.py")

def main():
    """Main deployment function"""
    print("🚀 ATS Buddy CloudFront Deployment (Non-Interactive)")
    print("=" * 55)
    print("This script will deploy ATS Buddy with secure CloudFront distribution")
    print("No user input required - uses sensible defaults")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Deploy infrastructure
    if not deploy_infrastructure():
        print("\n❌ Infrastructure deployment failed!")
        print("\n💡 If this is your first deployment, you may need to run:")
        print("   cd infra && sam deploy --guided")
        sys.exit(1)
    
    # Wait a moment for resources to be ready
    print("\n⏳ Waiting for resources to be ready...")
    time.sleep(10)
    
    # Get deployment outputs
    outputs = get_deployment_outputs()
    if not outputs:
        print("\n⚠️  Could not retrieve deployment outputs, but infrastructure may be deployed")
        print("💡 Try running: python scripts/deploy_web_ui.py")
        sys.exit(1)
    
    # Deploy web UI
    if not deploy_web_ui():
        print("\n⚠️  Web UI deployment failed, but infrastructure is deployed")
        print("💡 Try running: python scripts/deploy_web_ui.py")
        sys.exit(1)
    
    # Display summary
    display_deployment_summary(outputs)

if __name__ == "__main__":
    main()