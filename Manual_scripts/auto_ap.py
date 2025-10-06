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
        """Test GET operation (READ)"""
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
        """Test POST operation (CREATE)"""
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
    
    def test_put(self, endpoint: str = '', data: Dict = None, expected_status: int = 200, headers: Dict = None):
        """Test PUT operation (UPDATE - Full Replace)"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"PUT {url}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.put(url, json=data, headers=headers, timeout=10)
            
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
    
    def test_patch(self, endpoint: str = '', data: Dict = None, expected_status: int = 200, headers: Dict = None):
        """Test PATCH operation (UPDATE - Partial Update)"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"PATCH {url}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            
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
    
    def validate_response_data(self, response, expected_fields: List[str] = None):
        """Validate response contains expected fields"""
        try:
            data = response.json()
            
            if expected_fields:
                missing_fields = []
                for field in expected_fields:
                    # Handle nested field checks (e.g., "data.id")
                    if '.' in field:
                        parts = field.split('.')
                        current = data
                        for part in parts:
                            if isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                missing_fields.append(field)
                                break
                    else:
                        if field not in data:
                            missing_fields.append(field)
                
                if missing_fields:
                    return False, f"Missing fields: {', '.join(missing_fields)}"
                else:
                    return True, "All expected fields present"
            
            return True, "Response validated"
            
        except json.JSONDecodeError:
            return False, "Invalid JSON response"
    
    def run_full_crud_test(self, create_data: Dict = None, update_data: Dict = None, 
                           patch_data: Dict = None, expected_fields: List[str] = None):
        """Run complete CRUD test suite"""
        print("\n" + "="*70)
        print("Starting Complete CRUD API Automation Tests")
        print("="*70 + "\n")
        
        # Default test data if none provided
        if create_data is None:
            create_data = {
                "name": "Test Item",
                "description": "This is a test item",
                "value": 123
            }
        
        if update_data is None:
            update_data = {
                "name": "Updated Test Item",
                "description": "This item has been updated",
                "value": 456
            }
        
        if patch_data is None:
            patch_data = {
                "description": "Partially updated description"
            }
        
        resource_id = None
        
        # === CREATE (POST) ===
        print("\n--- 1. CREATE - POST Request ---")
        post_response = self.test_post(data=create_data)
        
        if post_response:
            # Validate response structure
            if expected_fields:
                is_valid, msg = self.validate_response_data(post_response, expected_fields)
                print(f"  Response Validation: {msg}")
            
            # Extract ID from response
            try:
                response_data = post_response.json()
                resource_id = (response_data.get('id') or 
                              response_data.get('_id') or 
                              response_data.get('uuid') or
                              response_data.get('data', {}).get('id'))
                
                if resource_id:
                    print(f"  ✓ Created resource with ID: {resource_id}")
            except:
                pass
        
        if not resource_id:
            print("\n⚠ Warning: Could not extract resource ID. Some tests will be skipped.")
        
        # === READ (GET ALL) ===
        print("\n--- 2. READ - GET All Resources ---")
        self.test_get()
        
        # === READ (GET SINGLE) ===
        if resource_id:
            print("\n--- 3. READ - GET Single Resource ---")
            get_response = self.test_get(endpoint=f"/{resource_id}")
            
            if get_response and expected_fields:
                is_valid, msg = self.validate_response_data(get_response, expected_fields)
                print(f"  Response Validation: {msg}")
        
        # === UPDATE (PUT - Full Update) ===
        if resource_id:
            print("\n--- 4. UPDATE - PUT Request (Full Update) ---")
            put_response = self.test_put(endpoint=f"/{resource_id}", data=update_data)
            
            # Verify the update
            if put_response:
                print("\n--- 5. Verify PUT Update - GET Request ---")
                verify_response = self.test_get(endpoint=f"/{resource_id}")
                
                if verify_response:
                    try:
                        verify_data = verify_response.json()
                        actual_data = verify_data.get('data', verify_data)
                        
                        # Check if updated fields match
                        mismatches = []
                        for key, value in update_data.items():
                            if actual_data.get(key) != value:
                                mismatches.append(f"{key}: expected '{value}', got '{actual_data.get(key)}'")
                        
                        if mismatches:
                            print(f"  ⚠ Update verification failed: {', '.join(mismatches)}")
                        else:
                            print(f"  ✓ PUT update verified successfully")
                    except:
                        pass
        
        # === UPDATE (PATCH - Partial Update) ===
        if resource_id:
            print("\n--- 6. UPDATE - PATCH Request (Partial Update) ---")
            patch_response = self.test_patch(endpoint=f"/{resource_id}", data=patch_data)
            
            # Verify the patch
            if patch_response:
                print("\n--- 7. Verify PATCH Update - GET Request ---")
                verify_response = self.test_get(endpoint=f"/{resource_id}")
                
                if verify_response:
                    try:
                        verify_data = verify_response.json()
                        actual_data = verify_data.get('data', verify_data)
                        
                        # Check if patched fields match
                        mismatches = []
                        for key, value in patch_data.items():
                            if actual_data.get(key) != value:
                                mismatches.append(f"{key}: expected '{value}', got '{actual_data.get(key)}'")
                        
                        if mismatches:
                            print(f"  ⚠ Patch verification failed: {', '.join(mismatches)}")
                        else:
                            print(f"  ✓ PATCH update verified successfully")
                    except:
                        pass
        
        # === DELETE ===
        if resource_id:
            print("\n--- 8. DELETE - DELETE Request ---")
            self.test_delete(endpoint=f"/{resource_id}")
            
            print("\n--- 9. Verify Deletion - GET Request (Should Fail) ---")
            self.test_get(endpoint=f"/{resource_id}", expected_status=404)
        
        # === EDGE CASE TESTS ===
        print("\n--- 10. Edge Cases & Error Handling ---")
        
        # Test GET non-existent resource
        print("\n  Testing GET non-existent resource:")
        self.test_get(endpoint="/nonexistent-id-12345", expected_status=404)
        
        # Test DELETE non-existent resource
        print("\n  Testing DELETE non-existent resource:")
        self.test_delete(endpoint="/nonexistent-id-12345", expected_status=404)
        
        # Test POST with invalid data
        print("\n  Testing POST with empty data:")
        self.test_post(data={}, expected_status=400)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("Test Summary Report")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✓ Passed: {passed} ({(passed/total*100):.1f}%)")
        print(f"✗ Failed: {failed} ({(failed/total*100):.1f}%)")
        
        if failed > 0:
            print("\n" + "-"*70)
            print("Failed Tests Details:")
            print("-"*70)
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"\n  ✗ {result['test']}")
                    print(f"    └─ {result['details']}")
        
        print("\n" + "="*70 + "\n")
        
        # Save results to file
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """Save test results to JSON file"""
        filename = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'summary': {
                        'total': len(self.results),
                        'passed': sum(1 for r in self.results if r['status'] == 'PASS'),
                        'failed': sum(1 for r in self.results if r['status'] == 'FAIL'),
                        'timestamp': datetime.now().isoformat()
                    },
                    'tests': self.results
                }, f, indent=2)
            print(f"✓ Test results saved to: {filename}")
        except Exception as e:
            print(f"✗ Could not save results: {str(e)}")


# Example usage
if __name__ == "__main__":
    # ========== CONFIGURATION - CHANGE THESE FOR YOUR API ==========
    
    API_URL = "http://127.0.0.1:5000/products"  # Your API endpoint
    
    # Optional: Add authentication headers
    HEADERS = {
        # "Authorization": "Bearer your_token_here",
        # "X-API-Key": "your_api_key_here",
    }
    
    # Data for CREATE operation
    CREATE_DATA = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 99.99,
        "stock": 50
    }
    
    # Data for UPDATE (PUT) operation - full replace
    UPDATE_DATA = {
        "name": "Updated Product",
        "description": "This product has been fully updated",
        "price": 149.99,
        "stock": 75
    }
    
    # Data for PATCH operation - partial update
    PATCH_DATA = {
        "price": 129.99,
        "stock": 100
    }
    
    # Expected fields in response (for validation)
    EXPECTED_FIELDS = ["id", "name", "description"]  # Adjust based on your API
    
    # ================================================================
    
    # Create tester instance
    tester = APITester(API_URL)
    
    # Run full CRUD test suite
    tester.run_full_crud_test(
        create_data=CREATE_DATA,
        update_data=UPDATE_DATA,
        patch_data=PATCH_DATA,
        expected_fields=EXPECTED_FIELDS
    )
    
    # ===== OR run individual tests =====
    # tester.test_get()
    # tester.test_post(data=CREATE_DATA)
    # tester.test_put(endpoint="/1", data=UPDATE_DATA)
    # tester.test_patch(endpoint="/1", data=PATCH_DATA)
    # tester.test_delete(endpoint="/1")
    # tester.print_summary()