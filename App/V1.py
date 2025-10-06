import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

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
    
    def test_get(self, endpoint: str = '', expected_status: int = 200, headers: Dict = None):
        """Test GET operation (READ)"""
        url = f"{self.base_url}{endpoint}"
        test_name = f"GET {url}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
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
        
        if create_data is None:
            create_data = {"name": "Test Item", "description": "Test", "value": 123}
        
        if update_data is None:
            update_data = {"name": "Updated Item", "description": "Updated", "value": 456}
        
        if patch_data is None:
            patch_data = {"description": "Partially updated"}
        
        resource_id = None
        
        # CREATE (POST)
        post_response = self.test_post(data=create_data)
        
        if post_response:
            if expected_fields:
                is_valid, msg = self.validate_response_data(post_response, expected_fields)
            
            try:
                response_data = post_response.json()
                resource_id = (response_data.get('id') or 
                              response_data.get('_id') or 
                              response_data.get('uuid') or
                              response_data.get('data', {}).get('id'))
            except:
                pass
        
        # READ (GET ALL)
        self.test_get()
        
        # READ (GET SINGLE)
        if resource_id:
            get_response = self.test_get(endpoint=f"/{resource_id}")
            
            if get_response and expected_fields:
                is_valid, msg = self.validate_response_data(get_response, expected_fields)
        
        # UPDATE (PUT)
        if resource_id:
            put_response = self.test_put(endpoint=f"/{resource_id}", data=update_data)
            
            if put_response:
                verify_response = self.test_get(endpoint=f"/{resource_id}")
        
        # UPDATE (PATCH)
        if resource_id:
            patch_response = self.test_patch(endpoint=f"/{resource_id}", data=patch_data)
            
            if patch_response:
                verify_response = self.test_get(endpoint=f"/{resource_id}")
        
        # DELETE
        if resource_id:
            self.test_delete(endpoint=f"/{resource_id}")
            self.test_get(endpoint=f"/{resource_id}", expected_status=404)
        
        # EDGE CASES
        self.test_get(endpoint="/nonexistent-id-12345", expected_status=404)
        self.test_delete(endpoint="/nonexistent-id-12345", expected_status=404)
        self.test_post(data={}, expected_status=400)
    
    def get_summary(self):
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = total - passed
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed/total*100) if total > 0 else 0
        }


def generate_pdf_report(tester: APITester, api_url: str):
    """Generate PDF report from test results"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph("API Test Report", title_style))
    story.append(Spacer(1, 12))
    
    # Test Info
    story.append(Paragraph(f"<b>API Endpoint:</b> {api_url}", styles['Normal']))
    story.append(Paragraph(f"<b>Test Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary
    summary = tester.get_summary()
    story.append(Paragraph("Test Summary", heading_style))
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Tests', str(summary['total'])],
        ['Passed', str(summary['passed'])],
        ['Failed', str(summary['failed'])],
        ['Pass Rate', f"{summary['pass_rate']:.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Test Results
    story.append(Paragraph("Detailed Test Results", heading_style))
    
    results_data = [['Test', 'Status', 'Details']]
    
    for result in tester.results:
        status_color = colors.green if result['status'] == 'PASS' else colors.red
        results_data.append([
            Paragraph(result['test'], styles['Normal']),
            Paragraph(f"<font color='{status_color.hexval()}'>{result['status']}</font>", styles['Normal']),
            Paragraph(result['details'][:100], styles['Normal'])
        ])
    
    results_table = Table(results_data, colWidths=[2.5*inch, 1*inch, 3*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    
    story.append(results_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# Streamlit UI
def main():
    st.set_page_config(page_title="API CRUD Tester", page_icon="🔧", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #1f77b4;
            color: white;
            font-weight: bold;
        }
        .success-box {
            padding: 1rem;
            background-color: #d4edda;
            border-left: 5px solid #28a745;
            margin: 1rem 0;
        }
        .fail-box {
            padding: 1rem;
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🔧 API CRUD Tester</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_url = st.text_input("API Endpoint URL", value="http://127.0.0.1:5000/items", 
                                help="Enter your API base URL")
        
        st.subheader("Authentication (Optional)")
        auth_type = st.selectbox("Auth Type", ["None", "Bearer Token", "API Key"])
        
        headers = {}
        if auth_type == "Bearer Token":
            token = st.text_input("Bearer Token", type="password")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "API Key":
            api_key = st.text_input("API Key", type="password")
            key_name = st.text_input("Key Name", value="X-API-Key")
            if api_key:
                headers[key_name] = api_key
        
        st.markdown("---")
        st.subheader("📊 Test Options")
        run_edge_cases = st.checkbox("Run Edge Case Tests", value=True)
        validate_fields = st.checkbox("Validate Response Fields", value=False)
    
    # Main Content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 CREATE Data (POST)")
        create_data = st.text_area("JSON Data for CREATE", 
            value='{\n  "name": "Test Product",\n  "description": "Test Description",\n  "price": 99.99,\n  "stock": 50\n}',
            height=150)
    
    with col2:
        st.subheader("✏️ UPDATE Data (PUT)")
        update_data = st.text_area("JSON Data for UPDATE", 
            value='{\n  "name": "Updated Product",\n  "description": "Updated Description",\n  "price": 149.99,\n  "stock": 75\n}',
            height=150)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🔧 PATCH Data (Partial Update)")
        patch_data = st.text_area("JSON Data for PATCH", 
            value='{\n  "price": 129.99,\n  "stock": 100\n}',
            height=100)
    
    with col4:
        st.subheader("✅ Expected Fields (Optional)")
        if validate_fields:
            expected_fields = st.text_input("Comma-separated fields", 
                value="id,name,description",
                help="e.g., id,name,data.user")
        else:
            expected_fields = ""
    
    st.markdown("---")
    
    # Run Tests Button
    if st.button("🚀 Run CRUD Tests", type="primary"):
        if not api_url:
            st.error("❌ Please enter an API URL")
            return
        
        try:
            # Parse JSON data
            create_json = json.loads(create_data)
            update_json = json.loads(update_data)
            patch_json = json.loads(patch_data)
            expected_fields_list = [f.strip() for f in expected_fields.split(",")] if expected_fields else None
            
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON format: {str(e)}")
            return
        
        # Run tests
        with st.spinner("Running tests... ⏳"):
            tester = APITester(api_url)
            tester.run_full_crud_test(
                create_data=create_json,
                update_data=update_json,
                patch_data=patch_json,
                expected_fields=expected_fields_list
            )
        
        # Display Results
        st.success("✅ Tests completed!")
        
        # Summary
        summary = tester.get_summary()
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Total Tests", summary['total'])
        col_b.metric("Passed ✅", summary['passed'])
        col_c.metric("Failed ❌", summary['failed'])
        col_d.metric("Pass Rate", f"{summary['pass_rate']:.1f}%")
        
        st.markdown("---")
        
        # Detailed Results
        st.subheader("📋 Detailed Test Results")
        
        for result in tester.results:
            if result['status'] == 'PASS':
                st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ {result['test']}</strong><br>
                        {result['details']}<br>
                        <small>🕒 {result['timestamp']}</small>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="fail-box">
                        <strong>❌ {result['test']}</strong><br>
                        {result['details']}<br>
                        <small>🕒 {result['timestamp']}</small>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Download Options
        st.subheader("📥 Download Test Report")
        
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            # JSON Download
            json_report = {
                'api_url': api_url,
                'timestamp': datetime.now().isoformat(),
                'summary': summary,
                'results': tester.results
            }
            
            st.download_button(
                label="📄 Download JSON Report",
                data=json.dumps(json_report, indent=2),
                file_name=f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col_download2:
            # PDF Download
            pdf_buffer = generate_pdf_report(tester, api_url)
            
            st.download_button(
                label="📕 Download PDF Report",
                data=pdf_buffer,
                file_name=f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )


if __name__ == "__main__":
    main()