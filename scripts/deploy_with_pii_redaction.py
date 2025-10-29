#!/usr/bin/env python3
"""
Deploy ATS Buddy with PII Redaction and CloudFront Security
Complete deployment script with enhanced security features
"""

import subprocess
import sys
import os
import json

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("🚀 ATS Buddy Secure Deployment (CloudFront + PII Redaction)")
    print("=" * 65)
    
    # Check if we're in the right directory
    if not os.path.exists("infra/template.yaml"):
        print("❌ Error: Please run this script from the ATS Buddy root directory")
        sys.exit(1)
    
    # Change to infra directory
    os.chdir("infra")
    
    # Build the SAM application with container-based build to avoid Python version issues
    print("\n🐳 Using container-based build to handle Python runtime compatibility...")
    build_cmd = "sam build --use-container"
    if not run_command(build_cmd, "Building SAM application (using containers)"):
        print("\n⚠️  Container build failed. Trying standard build...")
        if not run_command("sam build", "Building SAM application (standard)"):
            print("\n💡 Suggestion: Update your template.yaml to use python3.13 runtime")
            print("   Or install Python 3.13 to match your template runtime")
            sys.exit(1)
    
    # Deploy the application
    print("\n📋 Deploying with security enhancements...")
    print("This will:")
    print("- Create CloudFront distribution (no account ID exposure)")
    print("- Create S3 Object Lambda Access Point")
    print("- Deploy prebuilt PII redaction Lambda function")
    print("- Configure Amazon Comprehend integration")
    print("- Update existing Lambda with PII redaction support")
    print("- Secure S3 buckets (CloudFront access only)")
    
    deploy_cmd = "sam deploy --no-confirm-changeset --no-fail-on-empty-changeset"
    if not run_command(deploy_cmd, "Deploying infrastructure"):
        sys.exit(1)
    
    # Get stack outputs
    print("\n📊 Getting deployment information...")
    stack_name = "ats-buddy-dev"  # Default stack name
    
    outputs_cmd = f"aws cloudformation describe-stacks --stack-name {stack_name} --query 'Stacks[0].Outputs' --output json"
    outputs_result = run_command(outputs_cmd, "Retrieving stack outputs")
    
    if outputs_result:
        try:
            outputs = json.loads(outputs_result)
            
            print("\n🎉 Deployment completed successfully!")
            print("=" * 50)
            
            # Display key information
            if isinstance(outputs, list):
                for output in outputs:
                    key = output['OutputKey']
                    value = output['OutputValue']
                    
                    if 'PIIRedaction' in key:
                        print(f"🔒 {key}: {value}")
                    elif key in ['WebUIUrl', 'ApiGatewayUrl']:
                        print(f"🌐 {key}: {value}")
                    elif 'CloudFront' in key:
                        print(f"🌐 {key}: {value}")
            else:
                print("⚠️  Unexpected output format from CloudFormation")
            
            print("\n📋 Security Features:")
            print("✅ CloudFront CDN (no account ID exposure)")
            print("✅ HTTPS enforcement and global edge caching")
            print("✅ Amazon Comprehend PII detection")
            print("✅ Automatic PII masking with asterisks")
            print("✅ Private S3 buckets (CloudFront access only)")
            print("✅ Transparent integration with existing workflow")
            
            print("\n🔧 Next Steps:")
            print("1. Deploy Web UI: python scripts/deploy_web_ui.py")
            print("2. Test the secure system with CloudFront URL")
            print("3. Verify PII redaction in Textract output")
            print("4. Check CloudWatch logs for redaction activity")
            
        except json.JSONDecodeError:
            print("⚠️  Could not parse stack outputs, but deployment appears successful")
    
    print(f"\n✅ ATS Buddy with CloudFront security and PII redaction is ready!")

if __name__ == "__main__":
    main()