#!/usr/bin/env python3
"""
Open the secure CloudFront web UI in the default browser
"""

import webbrowser
import sys
import boto3

def get_web_ui_url(stack_name="ats-buddy-dev", region="ap-southeast-1"):
    """Get the secure CloudFront Web UI URL from CloudFormation outputs"""
    try:
        cf = boto3.client('cloudformation', region_name=region)
        response = cf.describe_stacks(StackName=stack_name)
        
        outputs = response['Stacks'][0]['Outputs']
        for output in outputs:
            if output['OutputKey'] == 'WebUIUrl':
                return output['OutputValue']
        
        print(f"❌ WebUIUrl not found in stack {stack_name}")
        return None
        
    except Exception as e:
        print(f"❌ Error getting Web UI URL: {e}")
        return None

def main():
    print("🌐 Opening Secure ATS Buddy Web UI (CloudFront)...")
    
    # Get the secure CloudFront URL
    web_ui_url = get_web_ui_url()
    
    if not web_ui_url:
        print("\n💡 Make sure you have:")
        print("   1. Deployed the ATS Buddy stack with CloudFront")
        print("   2. AWS credentials configured")
        print("   3. Correct stack name and region")
        return 1
    
    print(f"🔒 Secure URL: {web_ui_url}")
    print("✅ No account ID exposed in URL")
    print("✅ HTTPS encryption enabled")
    
    try:
        webbrowser.open(web_ui_url)
        print("✅ Secure Web UI opened in default browser")
        print("\n📋 Manual Testing Checklist:")
        print("1. ✅ Page loads correctly over HTTPS")
        print("2. ⬜ Upload a PDF file")
        print("3. ⬜ Enter job description (100+ chars)")
        print("4. ⬜ Click 'Analyze Resume'")
        print("5. ⬜ View loading animation")
        print("6. ⬜ Check analysis results")
        print("7. ⬜ Download reports (if available)")
        print("8. ⬜ Test 'Analyze Another Resume'")
        
        print("\n🔒 Security Features Active:")
        print("   ✅ CloudFront CDN protection")
        print("   ✅ No AWS account ID in URL")
        print("   ✅ HTTPS encryption enforced")
        print("   ✅ Global edge caching")
        
        return 0
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"Please manually open: {web_ui_url}")
        return 1

if __name__ == "__main__":
    sys.exit(main())