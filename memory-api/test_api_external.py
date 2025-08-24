#!/usr/bin/env python3
"""
ABOUTME: External API test script for BETTY Memory System v2.0
ABOUTME: Tests API endpoints via HTTP requests without internal imports
"""

import asyncio
import json
import time
import requests
from uuid import uuid4
from datetime import datetime
import sys

# Test configuration
BASE_URL = "http://localhost:8001"  # Docker container port
TIMEOUT = 10
TEST_HEADERS = {
    "Content-Type": "application/json",
    "API-Version": "2.0"
}

class BETTYAPITestSuite:
    """External API test suite for BETTY Memory System v2.0"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update(TEST_HEADERS)
        self.results = {
            "total": 0,
            "passed": 0, 
            "failed": 0,
            "errors": [],
            "details": []
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """Log test result"""
        self.results["total"] += 1
        if passed:
            self.results["passed"] += 1
            print(f"✅ {test_name}")
        else:
            self.results["failed"] += 1
            print(f"❌ {test_name}: {error}")
            self.results["errors"].append(f"{test_name}: {error}")
        
        if details:
            self.results["details"].append(f"{test_name}: {details}")
    
    def test_api_accessibility(self):
        """Test basic API accessibility"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            if response.status_code == 200:
                self.log_test("API Root Endpoint", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_test("API Root Endpoint", False, error=f"Status: {response.status_code}")
                return False
        except requests.RequestException as e:
            self.log_test("API Root Endpoint", False, error=str(e))
            return False
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            passed = response.status_code == 200
            self.log_test("Health Check", passed, 
                         f"Status: {response.status_code}" if passed else "",
                         f"Status: {response.status_code}" if not passed else "")
            return passed
        except requests.RequestException as e:
            self.log_test("Health Check", False, error=str(e))
            return False
    
    def test_version_info(self):
        """Test version information endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/version/info", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                version_detected = data.get("api_version") == "2.0"
                self.log_test("Version Info", version_detected, 
                             f"Version: {data.get('api_version')}")
                return version_detected
            else:
                self.log_test("Version Info", False, error=f"Status: {response.status_code}")
                return False
        except requests.RequestException as e:
            self.log_test("Version Info", False, error=str(e))
            return False
        except json.JSONDecodeError as e:
            self.log_test("Version Info", False, error=f"JSON decode error: {e}")
            return False
    
    def test_documentation_endpoints(self):
        """Test API documentation endpoints"""
        endpoints = [
            "/api/v2/docs/",
            "/api/v2/docs/openapi.json"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=TIMEOUT)
                passed = response.status_code == 200
                self.log_test(f"Documentation {endpoint}", passed,
                             f"Status: {response.status_code}" if passed else "",
                             f"Status: {response.status_code}" if not passed else "")
            except requests.RequestException as e:
                self.log_test(f"Documentation {endpoint}", False, error=str(e))
    
    def test_v2_features_endpoint(self):
        """Test v2 features listing"""
        try:
            response = self.session.get(f"{self.base_url}/version/features", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                v2_features = data.get("api_version") == "2.0" and "features" in data
                self.log_test("V2 Features", v2_features,
                             f"Features count: {len(data.get('features', []))}")
                return v2_features
            else:
                self.log_test("V2 Features", False, error=f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("V2 Features", False, error=str(e))
            return False
    
    def test_advanced_search_endpoint(self):
        """Test advanced search API (basic structure test)"""
        search_query = {
            "query": "test search",
            "search_type": "hybrid",
            "similarity_threshold": 0.75,
            "max_results": 10
        }
        
        try:
            # We expect this to fail with auth error (401/403) rather than 404
            response = self.session.post(f"{self.base_url}/api/v2/query/advanced-search", 
                                       json=search_query, timeout=TIMEOUT)
            
            # Endpoint exists if we get auth error rather than 404
            endpoint_exists = response.status_code != 404
            self.log_test("Advanced Search Endpoint", endpoint_exists,
                         f"Status: {response.status_code} (endpoint {'exists' if endpoint_exists else 'missing'})")
            return endpoint_exists
        except Exception as e:
            self.log_test("Advanced Search Endpoint", False, error=str(e))
            return False
    
    def test_batch_operations_endpoints(self):
        """Test batch operations endpoints availability"""
        endpoints = [
            "/api/v2/batch/operations",
            "/api/v2/batch/knowledge/import",
            "/api/v2/batch/knowledge/export"
        ]
        
        for endpoint in endpoints:
            try:
                # GET for operations list, POST for import/export
                method = "GET" if "operations" in endpoint else "POST"
                
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=TIMEOUT)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json={}, timeout=TIMEOUT)
                
                # Endpoint exists if we don't get 404
                exists = response.status_code != 404
                self.log_test(f"Batch {endpoint}", exists,
                             f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Batch {endpoint}", False, error=str(e))
    
    def test_cross_project_endpoints(self):
        """Test cross-project intelligence endpoints"""
        endpoints = [
            "/api/v2/cross-project/connections",
            "/api/v2/cross-project/search"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=TIMEOUT)
                exists = response.status_code != 404
                self.log_test(f"Cross-Project {endpoint}", exists,
                             f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Cross-Project {endpoint}", False, error=str(e))
    
    def test_webhook_endpoints(self):
        """Test webhook system endpoints"""
        endpoints = [
            ("/api/v2/webhooks/register", "POST"),
            ("/api/v2/webhooks/test", "POST")
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", 
                                               json={}, timeout=TIMEOUT)
                else:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=TIMEOUT)
                
                exists = response.status_code != 404
                self.log_test(f"Webhook {endpoint}", exists,
                             f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Webhook {endpoint}", False, error=str(e))
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid API version
            headers = self.session.headers.copy()
            headers["API-Version"] = "99.0"
            response = self.session.get(f"{self.base_url}/version/info", 
                                      headers=headers, timeout=TIMEOUT)
            
            error_handled = response.status_code == 400
            self.log_test("Error Handling", error_handled,
                         f"Invalid version status: {response.status_code}")
            return error_handled
        except Exception as e:
            self.log_test("Error Handling", False, error=str(e))
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting BETTY Memory System v2.0 Enhanced API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        api_accessible = self.test_api_accessibility()
        if not api_accessible:
            print("\n❌ API is not accessible. Stopping tests.")
            return self.results
        
        # Core functionality tests
        self.test_health_endpoint()
        self.test_version_info()
        self.test_v2_features_endpoint()
        self.test_documentation_endpoints()
        
        # v2.0 Enhanced API tests
        self.test_advanced_search_endpoint()
        self.test_batch_operations_endpoints()
        self.test_cross_project_endpoints()
        self.test_webhook_endpoints()
        
        # Error handling tests
        self.test_error_handling()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print(f"Total Tests: {self.results['total']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"Success Rate: {(self.results['passed']/self.results['total']*100):.1f}%")
        
        if self.results['errors']:
            print("\n🔍 Error Details:")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
        
        return self.results
    
    def check_service_health(self):
        """Quick service health check"""
        print("🔍 Checking service health...")
        
        # Check if service is running
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            print(f"API Status: {'✅ Running' if response.status_code == 200 else '❌ Error'}")
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"API Status: ❌ Not accessible ({e})")
            return False


if __name__ == "__main__":
    """Main execution"""
    test_suite = BETTYAPITestSuite()
    
    # Quick health check first
    if not test_suite.check_service_health():
        print("\n💡 Suggestions:")
        print("  1. Check if Docker containers are running: docker-compose ps")
        print("  2. Check container logs: docker logs betty_memory_api")
        print("  3. Try restarting: docker restart betty_memory_api")
        sys.exit(1)
    
    # Run full test suite
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["failed"] == 0 else 1)