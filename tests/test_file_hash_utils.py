"""
Unit tests for file hash utilities.
Tests SHA-256 hash calculation functionality.
"""

import pytest
import hashlib
from unittest.mock import Mock, patch
from src.file_hash_utils import calculate_file_hash, calculate_s3_file_hash


class TestCalculateFileHash:
    """Test cases for calculate_file_hash function."""
    
    def test_calculate_hash_with_valid_content(self):
        """Test hash calculation with valid file content."""
        # Test data
        test_content = b"This is test PDF content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Calculate hash
        result = calculate_file_hash(test_content)
        
        # Verify result
        assert result == expected_hash
        assert len(result) == 64  # SHA-256 produces 64-character hex string
    
    def test_calculate_hash_with_empty_content(self):
        """Test hash calculation with empty content raises ValueError."""
        with pytest.raises(ValueError, match="File content cannot be None or empty"):
            calculate_file_hash(b"")
    
    def test_calculate_hash_with_none_content(self):
        """Test hash calculation with None content raises ValueError."""
        with pytest.raises(ValueError, match="File content cannot be None or empty"):
            calculate_file_hash(None)
    
    def test_calculate_hash_consistency(self):
        """Test that same content produces same hash."""
        test_content = b"Consistent test content"
        
        hash1 = calculate_file_hash(test_content)
        hash2 = calculate_file_hash(test_content)
        
        assert hash1 == hash2
    
    def test_calculate_hash_different_content(self):
        """Test that different content produces different hashes."""
        content1 = b"First content"
        content2 = b"Second content"
        
        hash1 = calculate_file_hash(content1)
        hash2 = calculate_file_hash(content2)
        
        assert hash1 != hash2
    
    def test_calculate_hash_with_large_content(self):
        """Test hash calculation with large content."""
        # Create large test content (1MB)
        large_content = b"x" * (1024 * 1024)
        
        result = calculate_file_hash(large_content)
        
        assert len(result) == 64
        assert isinstance(result, str)


class TestCalculateS3FileHash:
    """Test cases for calculate_s3_file_hash function."""
    
    @patch('src.file_hash_utils.logger')
    def test_calculate_s3_hash_success(self, mock_logger):
        """Test successful S3 file hash calculation."""
        # Mock S3 client and response
        mock_s3_client = Mock()
        test_content = b"S3 file content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = test_content
        mock_s3_client.get_object.return_value = mock_response
        
        # Calculate hash
        result = calculate_s3_file_hash(mock_s3_client, "test-bucket", "test-key")
        
        # Verify result
        assert result == expected_hash
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="test-key")
    
    @patch('src.file_hash_utils.logger')
    def test_calculate_s3_hash_s3_error(self, mock_logger):
        """Test S3 file hash calculation with S3 error."""
        # Mock S3 client that raises exception
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = Exception("S3 error")
        
        # Calculate hash
        result = calculate_s3_file_hash(mock_s3_client, "test-bucket", "test-key")
        
        # Verify result
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('src.file_hash_utils.logger')
    def test_calculate_s3_hash_empty_file(self, mock_logger):
        """Test S3 file hash calculation with empty file."""
        # Mock S3 client with empty content
        mock_s3_client = Mock()
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = b""
        mock_s3_client.get_object.return_value = mock_response
        
        # Calculate hash - should return None due to empty content
        result = calculate_s3_file_hash(mock_s3_client, "test-bucket", "test-key")
        
        # Verify result
        assert result is None
        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])