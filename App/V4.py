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
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

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
    
    def test_request(self, method: str, endpoint: str = '', data: Dict = None, 
                    expected_status: int = 200, headers: Dict = None, test_name: str = None):
        """Generic test method for any HTTP method"""
        url = f"{self.base_url}{endpoint}"
        
        if test_name is None:
            test_name = f"{method} {url}"
        
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                self.log_result(test_name, 'FAIL', f"Unsupported method: {method}")
                return None
            
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
                    f"Expected status {expected_status}, got {response.status_code}. Response: {response.text[:150]}"
                )
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_result(test_name, 'FAIL', f"Error: {str(e)}")
            return None
    
    def run_ai_generated_tests(self, test_cases: List[Dict]):
        """Run AI-generated test cases"""
        for i, test_case in enumerate(test_cases, 1):
            method = test_case.get('method', 'GET')
            endpoint = test_case.get('endpoint', '')
            data = test_case.get('data')
            expected_status = test_case.get('expected_status', 200)
            description = test_case.get('description', f'Test {i}')
            
            test_name = f"[AI Test {i}] {description}"
            
            self.test_request(
                method=method,
                endpoint=endpoint,
                data=data,
                expected_status=expected_status,
                test_name=test_name
            )
    
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


class GeminiTestGenerator:
    def __init__(self, api_key: str):
        """Initialize Gemini AI"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_test_cases(self, api_url: str, sample_data: Dict, num_tests: int = 50, 
                           test_types: List[str] = None) -> List[Dict]:
        """Generate test cases using Gemini AI"""
        
        if test_types is None:
            test_types = ["happy_path", "edge_cases", "negative_tests", "security_tests"]
        
        prompt = f"""
You are an expert API testing specialist. Generate exactly {num_tests} comprehensive test cases for the following API:

API Endpoint: {api_url}
Sample Data Structure: {json.dumps(sample_data, indent=2)}

Generate test cases covering these categories:
{', '.join(test_types)}

For each test case, provide:
1. method: HTTP method (GET, POST, PUT, PATCH, DELETE)
2. endpoint: Additional path after base URL (e.g., "", "/123", "/invalid-id")
3. data: The request body (null for GET/DELETE)
4. expected_status: Expected HTTP status code (200, 201, 400, 404, etc.)
5. description: Clear description of what this test validates (use plain text, no special characters)
6. category: Type of test (happy_path, edge_case, negative_test, security_test)

Include diverse test cases:
- Happy path with valid data
- Boundary values (min/max lengths, zero, negative numbers)
- Invalid data types (string instead of number, etc.)
- Missing required fields
- Extra unexpected fields
- Empty/null values
- SQL injection attempts
- XSS attempts
- Very long strings (1000+ characters)
- Special characters and Unicode
- Invalid IDs for GET/PUT/PATCH/DELETE
- Malformed JSON structures

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON array
- NO markdown formatting, NO code blocks, NO explanations
- Use double quotes for all strings
- Ensure all JSON is properly escaped
- Use null (not None) for empty values
- Descriptions must use plain text only

Example format (replace with actual test cases):
[
  {{
    "method": "POST",
    "endpoint": "",
    "data": {{"name": "TestValue"}},
    "expected_status": 201,
    "description": "Valid POST request with all required fields",
    "category": "happy_path"
  }}
]
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # Aggressive cleaning of response
                if '```' in response_text:
                    import re
                    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
                    if match:
                        response_text = match.group(1)
                    else:
                        response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                # Remove any leading/trailing text before/after JSON array
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1:
                    response_text = response_text[start_idx:end_idx+1]
                
                # Try to parse
                test_cases = json.loads(response_text)
                
                # Validate structure
                if isinstance(test_cases, list) and len(test_cases) > 0:
                    valid_cases = []
                    for tc in test_cases:
                        if all(key in tc for key in ['method', 'expected_status', 'description']):
                            tc.setdefault('endpoint', '')
                            tc.setdefault('data', None)
                            tc.setdefault('category', 'other')
                            valid_cases.append(tc)
                    
                    if valid_cases:
                        return valid_cases
                
                if attempt < max_retries - 1:
                    st.warning(f"Attempt {attempt + 1} failed validation. Retrying...")
                    continue
                    
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    st.warning(f"Attempt {attempt + 1}: JSON parsing failed. Retrying...")
                    response_text = response_text.replace("'", '"')
                    response_text = response_text.replace('True', 'true').replace('False', 'false')
                    response_text = response_text.replace('None', 'null')
                    try:
                        test_cases = json.loads(response_text)
                        return test_cases
                    except:
                        continue
                else:
                    st.error(f"Failed to parse AI response after {max_retries} attempts")
                    return []
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    st.warning(f"Attempt {attempt + 1}: Error - {str(e)}. Retrying...")
                    continue
                else:
                    st.error(f"AI generation failed after {max_retries} attempts: {str(e)}")
                    return []
        
        return []
    
    def analyze_failures_and_generate_more(self, failed_tests: List[Dict], num_additional: int = 20) -> List[Dict]:
        """Analyze failed tests and generate more targeted test cases"""
        
        prompt = f"""
Analyze these failed API tests and generate {num_additional} additional targeted test cases:

Failed Tests:
{json.dumps(failed_tests[:10], indent=2)}

Based on the failure patterns, generate new test cases that explore similar issues.

Return ONLY a valid JSON array with this structure:
[
  {{
    "method": "POST",
    "endpoint": "",
    "data": {{"field": "value"}},
    "expected_status": 400,
    "description": "Test description",
    "category": "negative_test"
  }}
]

NO markdown, NO code blocks, ONLY the JSON array.
"""
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                response_text = response.text.strip()
                
                if '```' in response_text:
                    import re
                    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
                    if match:
                        response_text = match.group(1)
                    else:
                        response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']')
                
                if start_idx != -1 and end_idx != -1:
                    response_text = response_text[start_idx:end_idx+1]
                
                response_text = response_text.replace("'", '"').replace('True', 'true').replace('False', 'false').replace('None', 'null')
                
                test_cases = json.loads(response_text)
                
                if isinstance(test_cases, list) and len(test_cases) > 0:
                    return test_cases
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                else:
                    st.error(f"Failed to analyze failures: {str(e)}")
                    return []
        
        return []


def generate_pdf_report(tester: APITester, api_url: str):
    """Generate PDF report from test results"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
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
    
    story.append(Paragraph("API Test Report (AI-Generated)", title_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"<b>API Endpoint:</b> {api_url}", styles['Normal']))
    story.append(Paragraph(f"<b>Test Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
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
    
    story.append(Paragraph("Detailed Test Results", heading_style))
    
    results_data = [['Test', 'Status', 'Details']]
    
    for result in tester.results:
        status_color = colors.green if result['status'] == 'PASS' else colors.red
        results_data.append([
            Paragraph(result['test'][:60], styles['Normal']),
            Paragraph(f"<font color='{status_color.hexval()}'>{result['status']}</font>", styles['Normal']),
            Paragraph(result['details'][:80], styles['Normal'])
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
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def main():
    st.set_page_config(page_title="AI API Tester", page_icon="🤖", layout="wide")
    
    # Load Gemini API key from environment
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    
    # Check if API key is configured
    if not gemini_api_key:
        st.error("⚠️ GEMINI_API_KEY not found in .env file. Please configure it to use this application.")
        st.info("Create a .env file in the project root with: GEMINI_API_KEY=your_api_key_here")
        st.stop()
    
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.2rem;
            margin-bottom: 3rem;
        }
        .stButton>button {
            width: 100%;
            background-color: #1f77b4;
            color: white;
            font-weight: bold;
            padding: 0.75rem 1.5rem;
            font-size: 1.1rem;
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
        .info-box {
            padding: 1rem;
            background-color: #d1ecf1;
            border-left: 5px solid #0c5460;
            margin: 1rem 0;
        }
        .center-content {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🤖 AI-Powered API Tester</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Intelligent API Testing with Google Gemini AI</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'test_cases' not in st.session_state:
        st.session_state.test_cases = []
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    if 'api_url' not in st.session_state:
        st.session_state.api_url = "http://127.0.0.1:5000/items"
    
    # Main Content Tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Test Generation", "📊 Test Results", "📥 Download Reports"])
    
    with tab1:
        # Center the URL input
        st.markdown('<div class="center-content">', unsafe_allow_html=True)
        
        st.markdown("### 🌐 API Configuration")
        api_url = st.text_input(
            "Enter API Endpoint URL",
            value=st.session_state.api_url,
            placeholder="http://127.0.0.1:5000/items",
            help="Enter the base URL of your API endpoint",
            label_visibility="collapsed"
        )
        
        if api_url != st.session_state.api_url:
            st.session_state.api_url = api_url
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📝 Sample Data Structure")
            sample_data = st.text_area(
                "Provide a sample JSON structure for your API", 
                value='{\n  "name": "Product Name",\n  "description": "Product Description",\n  "price": 99.99,\n  "stock": 50,\n  "email": "user@example.com"\n}',
                height=250,
                help="This helps AI understand your API structure"
            )
        
        with col2:
            st.markdown("### ⚙️ Test Configuration")
            num_tests = st.slider("Number of Test Cases", min_value=10, max_value=500, value=50, step=10)
            
            st.markdown("**Test Categories:**")
            test_happy = st.checkbox("✅ Happy Path Tests", value=True)
            test_edge = st.checkbox("⚠️ Edge Cases", value=True)
            test_negative = st.checkbox("❌ Negative Tests", value=True)
            test_security = st.checkbox("🔒 Security Tests", value=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Generate AI Test Cases", type="primary"):
            if not api_url:
                st.error("❌ Please enter an API URL")
            else:
                try:
                    sample_json = json.loads(sample_data)
                    
                    test_types = []
                    if test_happy: test_types.append("happy_path")
                    if test_edge: test_types.append("edge_cases")
                    if test_negative: test_types.append("negative_tests")
                    if test_security: test_types.append("security_tests")
                    
                    with st.spinner("🤖 AI is generating intelligent test cases..."):
                        generator = GeminiTestGenerator(gemini_api_key)
                        test_cases = generator.generate_test_cases(
                            api_url=api_url,
                            sample_data=sample_json,
                            num_tests=num_tests,
                            test_types=test_types
                        )
                    
                    if test_cases:
                        st.session_state.test_cases = test_cases
                        st.success(f"✅ Generated {len(test_cases)} test cases!")
                        
                        # Show preview
                        st.markdown("### 📋 Test Case Preview (First 5)")
                        for i, tc in enumerate(test_cases[:5], 1):
                            with st.expander(f"Test {i}: {tc.get('description', 'N/A')}"):
                                st.json(tc)
                        
                        st.info(f"💡 {len(test_cases)} test cases ready to run. Go to 'Test Results' tab to execute!")
                    else:
                        st.error("❌ Failed to generate test cases. Please try again.")
                
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON in sample data")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Show generated test cases
        if st.session_state.test_cases:
            st.markdown("---")
            st.markdown(f"### 📦 Generated Test Cases: {len(st.session_state.test_cases)}")
            
            # Categorize tests
            categories = {}
            for tc in st.session_state.test_cases:
                cat = tc.get('category', 'other')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(tc)
            
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("😊 Happy Path", len(categories.get('happy_path', [])))
            col_b.metric("⚠️ Edge Cases", len(categories.get('edge_case', [])))
            col_c.metric("❌ Negative", len(categories.get('negative_test', [])))
            col_d.metric("🔒 Security", len(categories.get('security_test', [])))
            
            if st.button("▶️ Run All Test Cases", type="primary"):
                with st.spinner("Running tests... ⏳"):
                    tester = APITester(st.session_state.api_url)
                    tester.run_ai_generated_tests(st.session_state.test_cases)
                    st.session_state.test_results = tester
                
                st.success("✅ All tests completed!")
                st.info("👉 Go to 'Test Results' tab to see detailed results")
    
    with tab2:
        st.subheader("📊 Test Results")
        
        if st.session_state.test_results is None:
            st.info("ℹ️ No test results yet. Generate and run tests first!")
        else:
            tester = st.session_state.test_results
            summary = tester.get_summary()
            
            # Summary Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Tests", summary['total'])
            col2.metric("Passed ✅", summary['passed'])
            col3.metric("Failed ❌", summary['failed'])
            col4.metric("Pass Rate", f"{summary['pass_rate']:.1f}%")
            
            st.markdown("---")
            
            # Filter options
            filter_option = st.radio("Filter Results:", ["All", "Passed Only", "Failed Only"], horizontal=True)
            
            # Display Results
            st.markdown("### 📋 Detailed Test Results")
            
            filtered_results = tester.results
            if filter_option == "Passed Only":
                filtered_results = [r for r in tester.results if r['status'] == 'PASS']
            elif filter_option == "Failed Only":
                filtered_results = [r for r in tester.results if r['status'] == 'FAIL']
            
            for result in filtered_results:
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
            
            # AI Analysis of Failures
            if summary['failed'] > 0:
                st.markdown("---")
                st.markdown("### 🔍 AI Failure Analysis")
                
                if st.button("🤖 Analyze Failures & Generate More Tests"):
                    failed_tests = [r for r in tester.results if r['status'] == 'FAIL']
                    
                    with st.spinner("🤖 AI is analyzing failures and generating targeted tests..."):
                        generator = GeminiTestGenerator(gemini_api_key)
                        additional_tests = generator.analyze_failures_and_generate_more(failed_tests, num_additional=20)
                    
                    if additional_tests:
                        st.success(f"✅ Generated {len(additional_tests)} additional targeted tests!")
                        
                        # Add to existing test cases
                        st.session_state.test_cases.extend(additional_tests)
                        
                        # Preview
                        with st.expander("📋 View New Test Cases"):
                            for i, tc in enumerate(additional_tests, 1):
                                st.json(tc)
                        
                        if st.button("▶️ Run Additional Tests"):
                            with st.spinner("Running additional tests..."):
                                tester.run_ai_generated_tests(additional_tests)
                                st.session_state.test_results = tester
                            st.rerun()
    
    with tab3:
        st.subheader("📥 Download Test Reports")
        
        if st.session_state.test_results is None:
            st.info("ℹ️ No test results available for download yet.")
        else:
            tester = st.session_state.test_results
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📄 JSON Report")
                json_report = {
                    'api_url': st.session_state.api_url,
                    'timestamp': datetime.now().isoformat(),
                    'test_configuration': {
                        'total_tests_generated': len(st.session_state.test_cases),
                        'ai_powered': True
                    },
                    'summary': tester.get_summary(),
                    'results': tester.results,
                    'test_cases': st.session_state.test_cases
                }
                
                st.download_button(
                    label="📄 Download JSON Report",
                    data=json.dumps(json_report, indent=2),
                    file_name=f"ai_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                st.markdown("### 📕 PDF Report")
                pdf_buffer = generate_pdf_report(tester, st.session_state.api_url)
                
                st.download_button(
                    label="📕 Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"ai_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: gray;'>
            <p>🤖 Powered by Google Gemini AI | Built with Streamlit ❤️</p>
            <p><small>AI generates intelligent test cases covering happy paths, edge cases, negative scenarios, and security tests</small></p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()