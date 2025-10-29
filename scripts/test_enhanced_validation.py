#!/usr/bin/env python3
"""
Test the enhanced PDF validation
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, 'src')

from pdf_validator import PDFValidator

def main():
    # Load the payload
    with open('infra/my-s3-payload.json', 'r') as f:
        payload = json.load(f)
    
    bucket_name = payload['bucket_name']
    s3_key = payload['s3_key']
    
    print(f"Testing enhanced PDF validation for:")
    print(f"  Bucket: {bucket_name}")
    print(f"  Key: {s3_key}")
    print("-" * 50)
    
    validator = PDFValidator()
    
    # Test detailed file info
    print("Getting file information...")
    file_info = validator.get_detailed_file_info(bucket_name, s3_key)
    for key, value in file_info.items():
        print(f"  {key}: {value}")
    
    print("\nValidating PDF structure...")
    validation_result = validator.validate_pdf_structure(bucket_name, s3_key)
    
    if validation_result['valid']:
        print("✓ PDF structure validation passed")
        for key, value in validation_result.items():
            if key != 'valid':
                print(f"  {key}: {value}")
    else:
        print("✗ PDF structure validation failed")
        print(f"  Error: {validation_result['error']}")
        print(f"  Suggestion: {validation_result.get('suggestion', 'N/A')}")

if __name__ == "__main__":
    main()