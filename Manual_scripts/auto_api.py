import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import sys

class APITester:
    def __init__(self, base_url: str):
        """Initialize the API Tester with base URL"""
        self.base_url = base_url.rstrip('/')
        self.results = []
        
    def log_result(self, test_name: str, status: str, details: str):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.results.append(result)
        
        # Print colored output
        color = '\033[92m' if status == 'PASS' else '\033[91m'
        reset = '\033[0m'
        print(f"{color}[{status}]{reset} {test_name}: {details}")
    
    def test_get(self, endpoint: str = '', expected_status: int = 200, headers: Dict = None):
        """Test GET operation"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"GET {url}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # Check status code
            if response.status_code == expected_status:
                self.log_result(
                    test_name, 
                    'PASS', 
                    f"Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.2f}s"
                )
                return response
            else:
                self.log_result(
                    test_name, 
                    'FAIL', 
                    f"Expected status {expected_status}, got {response.status_code}"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_result(test_name, 'FAIL', f"Error: {str(e)}")
            return None
    
    def test_post(self, endpoint: str = '', data: Dict = None, expected_status: int = 201, headers: Dict = None):
        """Test POST operation"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"POST {url}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == expected_status:
                self.log_result(
                    test_name, 
                    'PASS', 
                    f"Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.2f}s"
                )
                return response
            else:
                self.log_result(
                    test_name, 
                    'FAIL', 
                    f"Expected status {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_result(test_name, 'FAIL', f"Error: {str(e)}")
            return None
    
    def test_delete(self, endpoint: str = '', expected_status: int = 200, headers: Dict = None):
        """Test DELETE operation"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"DELETE {url}"
        
        try:
            response = requests.delete(url, headers=headers, timeout=10)
            
            if response.status_code == expected_status:
                self.log_result(
                    test_name, 
                    'PASS', 
                    f"Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.2f}s"
                )
                return response
            else:
                self.log_result(
                    test_name, 
                    'FAIL', 
                    f"Expected status {expected_status}, got {response.status_code}"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_result(test_name, 'FAIL', f"Error: {str(e)}")
            return None
    
    def run_full_test_suite(self, test_data: Dict = None):
        """Run complete test suite for GET, POST, DELETE"""
        print("\n" + "="*70)
        print("Starting API Automation Tests")
        print("="*70 + "\n")
        
        # Default test data if none provided
        if test_data is None:
            test_data = {
                "name": "Test Item",
                "description": "This is a test",
                "value": 123
            }
        
        # Test 1: GET request (initial state)
        print("\n--- Test 1: GET Request (Initial) ---")
        get_response = self.test_get()
        
        # Test 2: POST request (create new resource)
        print("\n--- Test 2: POST Request (Create) ---")
        post_response = self.test_post(data=test_data)
        
        # Extract ID from POST response if available
        resource_id = None
        if post_response:
            try:
                response_data = post_response.json()
                # Try common ID field names
                resource_id = response_data.get('id') or response_data.get('_id') or response_data.get('uuid')
                if resource_id:
                    print(f"✓ Created resource with ID: {resource_id}")
            except:
                pass
        
        # Test 3: GET request (verify creation)
        if resource_id:
            print("\n--- Test 3: GET Request (Verify Creation) ---")
            self.test_get(endpoint=f"/{resource_id}")
        
        # Test 4: DELETE request
        if resource_id:
            print("\n--- Test 4: DELETE Request ---")
            self.test_delete(endpoint=f"/{resource_id}")
            
            # Test 5: GET request (verify deletion)
            print("\n--- Test 5: GET Request (Verify Deletion) ---")
            self.test_get(endpoint=f"/{resource_id}", expected_status=404)
        else:
            print("\n--- Test 4: DELETE Request (without ID) ---")
            self.test_delete()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("Test Summary")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("Failed Tests:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
        
        print("="*70 + "\n")


# Example usage
if __name__ == "__main__":
    # CONFIGURATION - Change these values for your API
    API_URL = "http://127.0.0.1:5000/items"  # Replace with your API
    
    # Optional: Add custom headers (like authentication tokens)
    HEADERS = {
        # "Authorization": "Bearer your_token_here",
        # "X-API-Key": "your_api_key_here"
    }
    
    # Optional: Custom test data for POST request
    TEST_DATA = {
        "name": "Apple"
    }
    
    # Create tester instance
    tester = APITester(API_URL)
    
    # Run full test suite
    tester.run_full_test_suite(test_data=TEST_DATA)
    
    # OR run individual tests
    # print("\n--- Running Individual Tests ---")
    # tester.test_get()
    # tester.test_post(data=TEST_DATA)
    # tester.test_delete(endpoint="/1")