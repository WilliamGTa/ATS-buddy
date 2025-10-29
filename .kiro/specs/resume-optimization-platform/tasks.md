# Implementation Plan (Streamlined for Hackathon POC)

**Overall Goal:** Demonstrate intelligent file management, temporary storage, and basic AI-powered resume enhancement in a single, working end-to-end flow.

**Key Prioritization:** Implement the most important features first and get them working before moving on to less critical elements. This should be more linear rather than many things at the same time.

## Phase 1: Core Deduplication and Storage (Get the Basics Working First)

- [x] 1. Set up DynamoDB and Basic Operations





  - Add DynamoDB table definition to SAM template for resume cache (ONLY `file_hash`, `extracted_text`, `original_filename`, `ttl`)
  - Update Lambda IAM permissions for DynamoDB access
  - Create basic DynamoDB client wrapper for cache put and get operations
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 2. Implement File Hash Calculation and Deduplication





  - Create SHA-256 hash function for PDF content
  - Implement cache lookup function
  - Add deduplication logic to Lambda to skip Textract (basic version: if hash exists, just return a canned "Deduplicated" message)
  - Write minimal unit tests for hash calculation
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Integrate Deduplication into Lambda (Basic)





  - Modify API Gateway handler to calculate hash before processing
  - Update workflow to check cache before calling Textract
  - Store extracted text in DynamoDB after Textract or loading from Cache
  - Add "Deduplicated" or "Processed" status to API response for user feedback
  - _Requirements: 1.5, 1.6_

## Phase 2: Resume Analysis and Enhancement (Add the AI)

- [x] 4. Enhanced Resume Generation Service (Simplified)





  - Implement `EnhancedResumeGenerator` class using existing Bedrock client with a simplified prompt that just focuses on adding missing keywords from the job description
  - Omit the improvement highlighting for now
  - The prompt should also make sure the generated data does not change the output format
  - Implement a function to generate a basic enhanced resume
  - _Requirements: 4.1, 4.2_

- [x] 5. Integrate Enhanced Resume into Workflow (Basic)





  - Add "Generate Enhanced Resume" option to analysis results (a simple button that triggers the Bedrock process)
  - Modify Lambda handler to support enhancement requests
  - Return the enhanced text in the API response
  - _Requirements: 4.1_

## Phase 3: Minimal UI Integration and Testing

- [x] 6. Basic UI Updates





  - Add deduplication status display
  - Implement text area to show the generated text
  - Add "Generate Enhanced Resume" button to trigger enhancement
  - _Requirements: 6.1, 6.3_

- [x] 7. Deploy and Test (End-to-End)





  - Deploy and test the entire workflow
  - Test same PDF uploaded multiple times to verify deduplication
  - Test enhanced resume generation with real data
  - _Requirements: 5.1, 5.2, 5.3_