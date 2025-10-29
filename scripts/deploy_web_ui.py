#!/usr/bin/env python3
"""
Deploy Web UI to S3 Bucket
Automatically gets the bucket name from CloudFormation and uploads web UI files
"""

import boto3
import os
import sys
from pathlib import Path

def get_deployment_info(stack_name="ats-buddy-dev", region="ap-southeast-1"):
    """Get deployment info from CloudFormation outputs"""
    try:
        cf = boto3.client('cloudformation', region_name=region)
        response = cf.describe_stacks(StackName=stack_name)
        
        outputs = response['Stacks'][0]['Outputs']
        info = {}
        
        for output in outputs:
            if output['OutputKey'] == 'WebUIBucketName':
                info['bucket_name'] = output['OutputValue']
            elif output['OutputKey'] == 'WebUIUrl':
                info['web_url'] = output['OutputValue']
            elif output['OutputKey'] == 'CloudFrontDistributionId':
                info['distribution_id'] = output['OutputValue']
        
        if 'bucket_name' not in info:
            print(f"❌ WebUIBucketName not found in stack {stack_name}")
            return None
            
        return info
        
    except Exception as e:
        print(f"❌ Error getting deployment info: {e}")
        return None

def upload_web_ui_files(bucket_name):
    """Upload web UI files to S3 bucket with proper content types"""
    try:
        s3 = boto3.client('s3')
        web_ui_dir = Path(__file__).parent.parent / 'web-ui'
        
        if not web_ui_dir.exists():
            print(f"❌ Web UI directory not found: {web_ui_dir}")
            return False
        
        # File mappings with content types
        files_to_upload = {
            'index.html': 'text/html',
            'script.js': 'application/javascript', 
            'styles.css': 'text/css'
        }
        
        print(f"📤 Uploading web UI files to s3://{bucket_name}/")
        
        for filename, content_type in files_to_upload.items():
            file_path = web_ui_dir / filename
            
            if file_path.exists():
                print(f"  Uploading {filename}")
                s3.upload_file(
                    str(file_path),
                    bucket_name,
                    filename,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'max-age=86400'  # 24 hours cache for static assets
                    }
                )
            else:
                print(f"  Warning: {filename} not found, skipping")
        
        return True
        
    except Exception as e:
        print(f"Error uploading files: {e}")
        return False

def invalidate_cloudfront_cache(distribution_id):
    """Invalidate CloudFront cache to ensure new files are served"""
    try:
        cloudfront = boto3.client('cloudfront')
        
        print(f"🔄 Invalidating CloudFront cache for distribution {distribution_id}")
        
        response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': f"deploy-{int(__import__('time').time())}"
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        print(f"✅ Cache invalidation created: {invalidation_id}")
        print("⏳ Note: Cache invalidation may take 5-15 minutes to complete")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Could not invalidate CloudFront cache: {e}")
        print("💡 You may need to wait for cache to expire or manually invalidate")
        return False

def main():
    """Main deployment function"""
    print("ATS Buddy Web UI Deployment (CloudFront)")
    print("=" * 45)
    
    # Get deployment info from CloudFormation
    print("📋 Getting deployment info from CloudFormation...")
    deploy_info = get_deployment_info()
    
    if not deploy_info:
        print("\n💡 Make sure you have:")
        print("   1. Deployed the ATS Buddy stack with SAM")
        print("   2. AWS credentials configured")
        print("   3. Correct stack name and region")
        sys.exit(1)
    
    bucket_name = deploy_info['bucket_name']
    web_url = deploy_info.get('web_url', 'Not available')
    distribution_id = deploy_info.get('distribution_id')
    
    print(f"✅ Found S3 bucket: {bucket_name}")
    if distribution_id:
        print(f"✅ Found CloudFront distribution: {distribution_id}")
    
    # Upload files
    print("\n📤 Uploading web UI files...")
    success = upload_web_ui_files(bucket_name)
    
    if success:
        print("\n🎉 Files uploaded successfully!")
        
        # Invalidate CloudFront cache if distribution exists
        if distribution_id:
            print("\n🔄 Invalidating CloudFront cache...")
            invalidate_cloudfront_cache(distribution_id)
        
        print(f"\n🌐 Web UI URL: {web_url}")
        print("\n🔒 Security Benefits:")
        print("   ✅ No account ID exposed in URL")
        print("   ✅ HTTPS encryption enabled")
        print("   ✅ Global CDN for fast loading")
        print("   ✅ Private S3 bucket (CloudFront access only)")
        
        if distribution_id:
            print("\n⏳ Note: If you don't see changes immediately, wait 5-15 minutes for cache invalidation")
        
        print("\n💡 You can now access your secure ATS Buddy web interface!")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()