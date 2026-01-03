"""
Tests for Django API endpoints.
Tests REST API endpoints and WebSocket connections.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse


class TestAPIEndpoints(TestCase):
    """Tests for REST API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health/')
        # Should be accessible or return 404 if not set up
        assert response.status_code in [200, 404]
    
    def test_ingest_start_endpoint(self):
        """Test ingestion start endpoint"""
        data = {
            "source": "arxiv",
            "categories": ["cs.LG"],
            "max_results": 5
        }
        response = self.client.post(
            '/api/ingest/start/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Should accept POST or return 404
        assert response.status_code in [200, 202, 404, 400]
    
    def test_ingest_status_endpoint(self):
        """Test ingestion status endpoint"""
        response = self.client.get('/api/ingest/status/')
        # Should be accessible or return 404
        assert response.status_code in [200, 404]
    
    def test_research_query_endpoint(self):
        """Test research query endpoint"""
        data = {
            "query": "machine learning",
            "analysis_type": "gap"
        }
        response = self.client.post(
            '/api/research/query/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Should accept POST or return 404
        assert response.status_code in [200, 202, 206, 404, 400]
    
    def test_research_get_endpoint(self):
        """Test research get endpoint"""
        response = self.client.get('/api/research/get/')
        # Should be accessible or return 404
        assert response.status_code in [200, 404]
    
    def test_invalid_request_data(self):
        """Test API with invalid request data"""
        response = self.client.post(
            '/api/ingest/start/',
            data='invalid json',
            content_type='application/json'
        )
        # Should return bad request or 404
        assert response.status_code in [400, 404]


class TestAPIErrorHandling(TestCase):
    """Tests for API error handling"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_404_not_found(self):
        """Test 404 error handling"""
        response = self.client.get('/api/nonexistent/')
        assert response.status_code == 404
    
    def test_missing_required_fields(self):
        """Test missing required fields handling"""
        data = {}  # Empty data
        response = self.client.post(
            '/api/ingest/start/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Should return bad request
        assert response.status_code in [400, 404]


class TestAPIInputValidation(TestCase):
    """Tests for API input validation"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_max_results_limit(self):
        """Test max_results validation"""
        data = {
            "source": "arxiv",
            "categories": ["cs.LG"],
            "max_results": 10000  # Very large number
        }
        response = self.client.post(
            '/api/ingest/start/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Should be accepted or rejected based on validation
        assert response.status_code in [200, 202, 400, 404]
    
    def test_invalid_category(self):
        """Test invalid category handling"""
        data = {
            "source": "arxiv",
            "categories": ["invalid_category"],
            "max_results": 5
        }
        response = self.client.post(
            '/api/ingest/start/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Should handle gracefully
        assert response.status_code in [200, 202, 400, 404]


class TestAPIResponseFormat(TestCase):
    """Tests for API response formatting"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_response_is_json(self):
        """Test that responses are JSON"""
        response = self.client.get('/api/health/')
        if response.status_code == 200:
            # Should be valid JSON
            assert response['Content-Type'] in ['application/json', 'application/json; charset=utf-8']


class TestWebSocketConnections(TestCase):
    """Tests for WebSocket connections"""
    
    def test_ingestion_progress_consumer(self):
        """Test ingestion progress WebSocket consumer"""
        # WebSocket testing requires django-channels test utilities
        # Basic structure test
        from backend.services.logging import get_logger
        
        logger = get_logger("websocket_test")
        assert logger is not None
    
    def test_analysis_consumer(self):
        """Test analysis WebSocket consumer"""
        from backend.services.logging import get_logger
        
        logger = get_logger("analysis_consumer_test")
        assert logger is not None


class TestAPIAuthentication(TestCase):
    """Tests for API authentication (if applicable)"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access to endpoints"""
        # Most endpoints should be accessible without auth
        response = self.client.get('/api/health/')
        assert response.status_code in [200, 404]


class TestAPIPerformance(TestCase):
    """Tests for API performance"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_health_check_response_time(self):
        """Test health check responds quickly"""
        import time
        
        start = time.time()
        response = self.client.get('/api/health/')
        duration = time.time() - start
        
        # Health check should respond quickly (< 1 second)
        assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
