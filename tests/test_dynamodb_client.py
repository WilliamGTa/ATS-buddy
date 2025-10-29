"""
Unit tests for DynamoDB client wrapper.
"""

import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dynamodb_client import DynamoDBClient


class TestDynamoDBClient:
    """Test cases for DynamoDB client wrapper."""
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_init_with_table_name(self):
        """Test DynamoDB client initialization with table name."""
        with patch('boto3.resource') as mock_resource:
            mock_dynamodb = Mock()
            mock_table = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            assert client.table_name == 'test-resume-cache'
            mock_resource.assert_called_once_with('dynamodb')
            mock_dynamodb.Table.assert_called_once_with('test-resume-cache')
    
    def test_init_without_table_name(self):
        """Test DynamoDB client initialization fails without table name."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('boto3.resource'):
                with pytest.raises(ValueError, match="RESUME_CACHE_TABLE environment variable not set"):
                    DynamoDBClient()
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_put_resume_cache_success(self):
        """Test successful resume cache storage."""
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            # Mock successful put_item
            mock_table.put_item.return_value = {}
            
            result = client.put_resume_cache(
                file_hash='abc123',
                extracted_text='Sample resume text',
                original_filename='resume.pdf'
            )
            
            assert result is True
            mock_table.put_item.assert_called_once()
            
            # Verify the item structure
            call_args = mock_table.put_item.call_args
            item = call_args[1]['Item']
            assert item['file_hash'] == 'abc123'
            assert item['extracted_text'] == 'Sample resume text'
            assert item['original_filename'] == 'resume.pdf'
            assert 'ttl' in item
            assert isinstance(item['ttl'], int)
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_get_resume_cache_found(self):
        """Test successful resume cache retrieval."""
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            # Mock successful get_item with data
            mock_table.get_item.return_value = {
                'Item': {
                    'file_hash': 'abc123',
                    'extracted_text': 'Sample resume text',
                    'original_filename': 'resume.pdf',
                    'ttl': int(time.time()) + 86400
                }
            }
            
            result = client.get_resume_cache('abc123')
            
            assert result is not None
            assert result['file_hash'] == 'abc123'
            assert result['extracted_text'] == 'Sample resume text'
            assert result['original_filename'] == 'resume.pdf'
            assert 'ttl' in result
            
            mock_table.get_item.assert_called_once_with(Key={'file_hash': 'abc123'})
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_get_resume_cache_not_found(self):
        """Test resume cache retrieval when item not found."""
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            # Mock get_item with no data
            mock_table.get_item.return_value = {}
            
            result = client.get_resume_cache('nonexistent')
            
            assert result is None
            mock_table.get_item.assert_called_once_with(Key={'file_hash': 'nonexistent'})
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_cache_exists_true(self):
        """Test cache_exists returns True when cache exists."""
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            # Mock get_item with data
            mock_table.get_item.return_value = {
                'Item': {
                    'file_hash': 'abc123',
                    'extracted_text': 'Sample resume text',
                    'original_filename': 'resume.pdf',
                    'ttl': int(time.time()) + 86400
                }
            }
            
            result = client.cache_exists('abc123')
            
            assert result is True
    
    @patch.dict(os.environ, {'RESUME_CACHE_TABLE': 'test-resume-cache'})
    def test_cache_exists_false(self):
        """Test cache_exists returns False when cache doesn't exist."""
        with patch('boto3.resource') as mock_resource:
            mock_table = Mock()
            mock_dynamodb = Mock()
            mock_resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            client = DynamoDBClient()
            
            # Mock get_item with no data
            mock_table.get_item.return_value = {}
            
            result = client.cache_exists('nonexistent')
            
            assert result is False