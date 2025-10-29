#!/usr/bin/env python3
"""
Check available Bedrock inference profiles
"""

import boto3
import json
from botocore.exceptions import ClientError

def check_inference_profiles():
    """Check available inference profiles"""
    print("🔍 Checking Bedrock Inference Profiles...")
    
    try:
        bedrock = boto3.client('bedrock')
        
        # List inference profiles
        response = bedrock.list_inference_profiles()
        
        profiles = response.get('inferenceProfileSummaries', [])
        print(f"✅ Found {len(profiles)} inference profiles")
        
        for profile in profiles:
            profile_id = profile['inferenceProfileId']
            profile_name = profile['inferenceProfileName']
            status = profile['status']
            models = profile.get('models', [])
            
            print(f"\n📋 Profile: {profile_name}")
            print(f"   ID: {profile_id}")
            print(f"   Status: {status}")
            print(f"   Models: {len(models)}")
            
            for model in models:
                model_id = model.get('modelId', 'Unknown')
                print(f"     - {model_id}")
        
        return profiles
        
    except ClientError as e:
        print(f"❌ Error checking inference profiles: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

def test_inference_profile(profile_id):
    """Test a specific inference profile"""
    print(f"🧪 Testing inference profile: {profile_id}")
    
    try:
        bedrock = boto3.client('bedrock-runtime')
        
        request_body = {
            "messages": [{"role": "user", "content": [{"text": "Hello, respond with 'Connection successful'"}]}],
            "inferenceConfig": {
                "max_new_tokens": 50,
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        response = bedrock.invoke_model(
            modelId=profile_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'output' in response_body and 'message' in response_body['output']:
            content = response_body['output']['message']['content'][0]['text']
            print(f"   ✅ Success: {content}")
            return True
        else:
            print(f"   ❌ Unexpected response format")
            return False
            
    except ClientError as e:
        print(f"   ❌ Failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def get_current_model():
    """Get the currently configured model from bedrock_client.py"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        from bedrock_client import BedrockClient
        
        client = BedrockClient()
        return client.model_id
    except Exception:
        return None

def rank_models(working_profiles):
    """Rank models by capability (best to worst)"""
    # Model ranking by capability and cost-effectiveness
    model_ranking = {
        'nova-pro': 1,    # Most capable
        'nova-lite': 2,   # Best balance (recommended)
        'nova-micro': 3,  # Fastest/cheapest but less capable
        'claude-3-5-sonnet': 4,  # Good but expensive
        'claude-3-sonnet': 5,
        'claude-3-haiku': 6
    }
    
    def get_model_rank(profile_id):
        for model_type, rank in model_ranking.items():
            if model_type in profile_id.lower():
                return rank
        return 999  # Unknown models go last
    
    return sorted(working_profiles, key=get_model_rank)

def main():
    """Check inference profiles and test them"""
    print("🎯 BEDROCK INFERENCE PROFILES CHECK")
    print("=" * 50)
    
    # Get current model configuration
    current_model = get_current_model()
    if current_model:
        print(f"📋 Current model in bedrock_client.py: {current_model}")
    
    # Check available profiles
    profiles = check_inference_profiles()
    
    if not profiles:
        print("\n❌ No inference profiles found")
        print("🔧 You may need to create inference profiles in AWS Console")
        return
    
    # Test each profile
    working_profiles = []
    
    for profile in profiles:
        profile_id = profile['inferenceProfileId']
        if test_inference_profile(profile_id):
            working_profiles.append(profile_id)
    
    print("\n" + "=" * 50)
    print("🏆 RESULTS")
    print("=" * 50)
    
    if working_profiles:
        print(f"✅ Found {len(working_profiles)} working inference profiles:")
        
        # Rank models by capability
        ranked_models = rank_models(working_profiles)
        
        for i, profile_id in enumerate(ranked_models):
            capability = "🥇 Most Capable" if i == 0 else "🥈 Balanced" if i == 1 else "🥉 Fast/Cheap" if i == 2 else "📊 Available"
            current_marker = " ← CURRENT" if profile_id == current_model else ""
            print(f"   {capability}: {profile_id}{current_marker}")
        
        # Smart recommendation
        print(f"\n💡 RECOMMENDATION:")
        
        if current_model and current_model in working_profiles:
            # Current model is working
            current_rank = next((i for i, model in enumerate(ranked_models) if model == current_model), -1)
            
            if current_rank <= 1:  # Using top 2 models
                print(f"   ✅ Your current model ({current_model}) is excellent!")
                print(f"   🎯 No changes needed - you're using a top-tier model")
            else:
                better_options = ranked_models[:2]  # Top 2 models
                available_better = [m for m in better_options if m != current_model]
                if available_better:
                    print(f"   🔄 Consider upgrading to: {available_better[0]}")
                    print(f"   📈 This would improve analysis quality")
                else:
                    print(f"   ✅ Your current model is good!")
        else:
            # Current model not working or not found
            recommended = ranked_models[1] if len(ranked_models) > 1 else ranked_models[0]  # Prefer nova-lite
            print(f"   🔧 Update bedrock_client.py model_id to: {recommended}")
            print(f"   📝 This is the recommended balance of performance and cost")
        
        return ranked_models[0] if ranked_models else None
    else:
        print("❌ No working inference profiles found")
        print("🔧 Check AWS Console for inference profile setup")
        return None

if __name__ == "__main__":
    main()