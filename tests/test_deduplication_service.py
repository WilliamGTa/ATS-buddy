"""
Unit tests for deduplication service.
Tests file deduplication logic and cache operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.deduplication_service import DeduplicationService


class TestDeduplicationService:
    """Test cases for DeduplicationService class."""
    
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_init(self, mock_boto3, mock_dynamodb_client):
        """Test DeduplicationService initialization."""
        service = DeduplicationService()
        
        assert service.s3_client is not None
        assert service.dynamodb_client is not None
        mock_boto3.client.assert_called_once_with('s3')
    
    @patch('src.deduplication_service.calculate_s3_file_hash')
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_check_file_deduplication_unique_file(self, mock_boto3, mock_dynamodb_client, mock_hash_func):
        """Test deduplication check for unique file."""
        # Setup mocks
        mock_hash_func.return_value = "abc123hash"
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.get_resume_cache.return_value = None
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test unique file
        result = service.check_file_deduplication("test-bucket", "test-key", "test.pdf")
        
        # Verify result
        assert result["is_duplicate"] is False
        assert result["file_hash"] == "abc123hash"
        assert result["cached_data"] is None
        assert "unique" in result["message"].lower()
        mock_hash_func.assert_called_once()
        mock_dynamodb_instance.get_resume_cache.assert_called_once_with("abc123hash")
    
    @patch('src.deduplication_service.calculate_s3_file_hash')
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_check_file_deduplication_duplicate_file(self, mock_boto3, mock_dynamodb_client, mock_hash_func):
        """Test deduplication check for duplicate file."""
        # Setup mocks
        mock_hash_func.return_value = "abc123hash"
        cached_data = {
            "file_hash": "abc123hash",
            "extracted_text": "Cached resume text",
            "original_filename": "original.pdf",
            "ttl": 1234567890
        }
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.get_resume_cache.return_value = cached_data
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test duplicate file
        result = service.check_file_deduplication("test-bucket", "test-key", "test.pdf")
        
        # Verify result
        assert result["is_duplicate"] is True
        assert result["file_hash"] == "abc123hash"
        assert result["cached_data"] == cached_data
        assert "already processed" in result["message"].lower()
        mock_hash_func.assert_called_once()
        mock_dynamodb_instance.get_resume_cache.assert_called_once_with("abc123hash")
    
    @patch('src.deduplication_service.calculate_s3_file_hash')
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_check_file_deduplication_hash_failure(self, mock_boto3, mock_dynamodb_client, mock_hash_func):
        """Test deduplication check when hash calculation fails."""
        # Setup mocks
        mock_hash_func.return_value = None
        mock_dynamodb_instance = Mock()
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test hash failure
        result = service.check_file_deduplication("test-bucket", "test-key", "test.pdf")
        
        # Verify result
        assert result["is_duplicate"] is False
        assert result["file_hash"] is None
        assert result["cached_data"] is None
        assert "error" in result
        mock_hash_func.assert_called_once()
        mock_dynamodb_instance.get_resume_cache.assert_not_called()
    
    @patch('src.deduplication_service.calculate_s3_file_hash')
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_check_file_deduplication_exception(self, mock_boto3, mock_dynamodb_client, mock_hash_func):
        """Test deduplication check when exception occurs."""
        # Setup mocks
        mock_hash_func.side_effect = Exception("Test exception")
        mock_dynamodb_instance = Mock()
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test exception handling
        result = service.check_file_deduplication("test-bucket", "test-key", "test.pdf")
        
        # Verify result
        assert result["is_duplicate"] is False
        assert result["file_hash"] is None
        assert result["cached_data"] is None
        assert "error" in result
        assert "Test exception" in result["error"]
    
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_store_processed_file_success(self, mock_boto3, mock_dynamodb_client):
        """Test successful storage of processed file."""
        # Setup mocks
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.put_resume_cache.return_value = True
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test successful storage
        result = service.store_processed_file("abc123hash", "Resume text", "test.pdf")
        
        # Verify result
        assert result is True
        mock_dynamodb_instance.put_resume_cache.assert_called_once_with(
            file_hash="abc123hash",
            extracted_text="Resume text",
            original_filename="test.pdf"
        )
    
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_store_processed_file_failure(self, mock_boto3, mock_dynamodb_client):
        """Test failed storage of processed file."""
        # Setup mocks
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.put_resume_cache.return_value = False
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test failed storage
        result = service.store_processed_file("abc123hash", "Resume text", "test.pdf")
        
        # Verify result
        assert result is False
        mock_dynamodb_instance.put_resume_cache.assert_called_once()
    
    @patch('src.deduplication_service.DynamoDBClient')
    @patch('src.deduplication_service.boto3')
    def test_store_processed_file_exception(self, mock_boto3, mock_dynamodb_client):
        """Test storage of processed file with exception."""
        # Setup mocks
        mock_dynamodb_instance = Mock()
        mock_dynamodb_instance.put_resume_cache.side_effect = Exception("Storage error")
        mock_dynamodb_client.return_value = mock_dynamodb_instance
        
        service = DeduplicationService()
        
        # Test exception handling
        result = service.store_processed_file("abc123hash", "Resume text", "test.pdf")
        
        # Verify result
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])