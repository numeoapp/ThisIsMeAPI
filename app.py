"""
Railway Flask API for ThisIsMe Integration - Multiple APIs
Supports: DataPro and Trace APIs
Save this as: app.py
"""

from flask import Flask, request, jsonify, Response
import requests
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Certificate paths
CERT_PATH = "www.fxcloudv2.co.za.pem"
KEY_PATH = "fxcloud.key"

BASE_URL = "https://uat-api.thisisme.com"

# API Key for security
API_KEY = os.environ.get('API_KEY', 'dreamteam91frag').strip()

def verify_api_key():
    """Check if the API key is valid"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    token = auth_header.replace('Bearer ', '').strip()
    return token == API_KEY

# ============================================================================
# DATAPRO API FUNCTIONS
# ============================================================================

def submit_datapro_verification(identity_number, reference=None):
    """Submit ID to ThisIsMe DataPro API"""
    url = f"{BASE_URL}/dhadatapro/"
    headers = {'content-type': 'application/json'}

    payload = {
        "identity_number": identity_number,
        "disable_report": "false"
    }

    if reference:
        payload["reference"] = reference

    try:
        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e), "type": type(e).__name__}

def get_datapro_results(request_id, max_attempts=10):
    """Retrieve DataPro verification results"""
    url = f"{BASE_URL}/v4/dhadatapro/{request_id}"
    headers = {'content-type': 'application/json'}

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                url,
                verify=False,
                headers=headers,
                cert=(CERT_PATH, KEY_PATH),
                timeout=30
            )

            result = response.json()
            status_code = response.status_code

            if status_code in [200, 206, 227]:
                return status_code, result
            elif status_code in [303, 429]:
                if attempt < max_attempts - 1:
                    time.sleep(5 if status_code == 429 else 3)
                    continue
                else:
                    return status_code, result
            else:
                return status_code, result

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            else:
                return 500, {"error": str(e), "type": type(e).__name__}

    return 408, {"status": "TIMEOUT", "message": "Request timed out"}

# ============================================================================
# TRACE API FUNCTIONS
# ============================================================================

def submit_trace_request(identity_number, reference=None):
    """Submit ID to ThisIsMe Trace API"""
    url = f"{BASE_URL}/trace/"
    headers = {'content-type': 'application/json'}

    payload = {
        "identity_number": identity_number,
        "disable_report": "false"
    }

    if reference:
        payload["reference"] = reference

    try:
        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e), "type": type(e).__name__}

def get_trace_results(request_id, max_attempts=10):
    """Retrieve Trace results"""
    url = f"{BASE_URL}/v4/trace/{request_id}"
    headers = {'content-type': 'application/json'}

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                url,
                verify=False,
                headers=headers,
                cert=(CERT_PATH, KEY_PATH),
                timeout=30
            )

            result = response.json()
            status_code = response.status_code

            if status_code in [200, 227]:
                return status_code, result
            elif status_code in [303, 429]:
                if attempt < max_attempts - 1:
                    time.sleep(5 if status_code == 429 else 3)
                    continue
                else:
                    return status_code, result
            else:
                return status_code, result

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            else:
                return 500, {"error": str(e), "type": type(e).__name__}

    return 408, {"status": "TIMEOUT", "message": "Request timed out"}

def extract_trace_data(trace_data):
    """Extract specific fields from Trace API response"""
    extracted = {
        "address": None,
        "employer": None,
        "cell_number": None
    }

    # Get response data
    response_list = trace_data.get("response", [])
    if not response_list or len(response_list) == 0:
        return extracted

    response_data = response_list[0]

    # Extract first address
    addresses = response_data.get("addresses", [])
    if addresses and len(addresses) > 0:
        first_address = addresses[0]
        extracted["address"] = {
            "line1": first_address.get("adrs_line1"),
            "line2": first_address.get("adrs_line2"),
            "line3": first_address.get("adrs_line3"),
            "line4": first_address.get("adrs_line4"),
            "type": first_address.get("adrs_type"),
            "postal_code": first_address.get("postal_code"),
            "created_date": first_address.get("created_date"),
            "last_updated": first_address.get("last_updated")
        }

    # Extract first employer
    employers = response_data.get("employers", [])
    if employers and len(employers) > 0:
        first_employer = employers[0]
        extracted["employer"] = {
            "name": first_employer.get("emp_name"),
            "occupation": first_employer.get("occupation"),
            "branch_code": first_employer.get("branch_code"),
            "created_date": first_employer.get("created_date"),
            "last_updated": first_employer.get("last_updated")
        }

    # Extract first CELL telephone
    telephones = response_data.get("telephones", [])
    for phone in telephones:
        if phone.get("telephone_type") == "CELL":
            extracted["cell_number"] = {
                "number": phone.get("telephone"),
                "created_date": phone.get("created_date"),
                "last_updated": phone.get("last_updated")
            }
            break  # Only get the first CELL number

    return extracted

# ============================================================================
# AML RISK SEARCH API FUNCTIONS
# ============================================================================

def submit_aml_verification(first_name, surname, middle_name=None, date_of_birth=None, country=None, reference=None):
    """Submit an individual to ThisIsMe AML Risk Search (sanctions/PEP/adverse-media) API"""
    url = f"{BASE_URL}/amlrisk/search/"
    headers = {'content-type': 'application/json'}

    payload = {
        "first_name": first_name,
        "surname": surname,
        "disable_report": "false"
    }

    if middle_name:
        payload["middle_name"] = middle_name
    if date_of_birth:
        payload["date_of_birth"] = date_of_birth
    if country:
        payload["country"] = country
    if reference:
        payload["reference"] = reference

    try:
        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e), "type": type(e).__name__}

def get_aml_results(request_id, max_attempts=10):
    """Retrieve AML Risk Search results"""
    url = f"{BASE_URL}/v4/amlrisk/search/{request_id}"
    headers = {'content-type': 'application/json'}

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                url,
                verify=False,
                headers=headers,
                cert=(CERT_PATH, KEY_PATH),
                timeout=30
            )

            result = response.json()
            status_code = response.status_code

            if status_code in [200, 206, 227]:
                return status_code, result
            elif status_code in [303, 429]:
                if attempt < max_attempts - 1:
                    time.sleep(5 if status_code == 429 else 3)
                    continue
                else:
                    return status_code, result
            else:
                return status_code, result

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            else:
                return 500, {"error": str(e), "type": type(e).__name__}

    return 408, {"status": "TIMEOUT", "message": "Request timed out"}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Health check"""
    return jsonify({
        "status": "online",
        "service": "ThisIsMe API Middleware",
        "version": "2.1",
        "endpoints": {
            "verify": "POST /verify (DataPro only)",
            "trace": "POST /trace (Trace only)",
            "aml": "POST /aml (AML Risk Search only)",
            "verify_all": "POST /verify-all (DataPro + Trace + AML combined)",
            "check_datapro": "GET /check/datapro/{request_id}",
            "check_trace": "GET /check/trace/{request_id}",
            "download_attachment": "POST /download-attachment"
        }
    })

@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({"status": "healthy"}), 200

@app.route('/verify', methods=['POST'])
def verify_id():
    """Verify ID - DataPro only (original endpoint)"""

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized - Invalid or missing API key"
        }), 401

    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400

    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400

    identity_number = data.get('identity_number')
    reference = data.get('reference', '')

    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400

    # Submit DataPro verification
    submit_status, submit_response = submit_datapro_verification(identity_number, reference)

    if submit_status != 303 and submit_status != 200:
        return jsonify({
            "success": False,
            "error": "Failed to submit verification",
            "status_code": submit_status,
            "response": submit_response
        }), submit_status

    request_id = submit_response.get('request_id')

    if not request_id:
        return jsonify({
            "success": False,
            "error": "No request_id received",
            "response": submit_response
        }), 500

    time.sleep(2)

    result_status, results = get_datapro_results(request_id)

    return jsonify({
        "success": result_status in [200, 206, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/trace', methods=['POST'])
def trace_id():
    """Trace ID - Trace API only"""

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400

    identity_number = data.get('identity_number')
    reference = data.get('reference', '')

    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400

    # Submit Trace request
    submit_status, submit_response = submit_trace_request(identity_number, reference)

    if submit_status != 303 and submit_status != 200:
        return jsonify({
            "success": False,
            "error": "Failed to submit trace request",
            "status_code": submit_status,
            "response": submit_response
        }), submit_status

    request_id = submit_response.get('request_id')

    if not request_id:
        return jsonify({
            "success": False,
            "error": "No request_id received",
            "response": submit_response
        }), 500

    time.sleep(2)

    result_status, results = get_trace_results(request_id)

    # Extract specific data
    extracted = extract_trace_data(results)

    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results,
        "extracted": extracted
    })

@app.route('/verify-all', methods=['POST'])
def verify_all():
    """
    Comprehensive verification - Calls both DataPro and Trace APIs
    Returns combined data
    """

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400

    identity_number = data.get('identity_number')
    reference = data.get('reference', '')

    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400

    combined_results = {
        "identity_number": identity_number,
        "datapro": None,
        "trace": None,
        "aml": None
    }

    # 1. Call DataPro API
    submit_status, submit_response = submit_datapro_verification(identity_number, reference)

    if submit_status in [200, 303]:
        datapro_request_id = submit_response.get('request_id')
        if datapro_request_id:
            time.sleep(2)
            datapro_status, datapro_results = get_datapro_results(datapro_request_id)
            combined_results["datapro"] = {
                "success": datapro_status in [200, 206, 227],
                "status_code": datapro_status,
                "request_id": datapro_request_id,
                "data": datapro_results
            }
        else:
            combined_results["datapro"] = {
                "success": False,
                "status_code": submit_status,
                "error": "No request_id received",
                "response": submit_response
            }
    else:
        combined_results["datapro"] = {
            "success": False,
            "status_code": submit_status,
            "error": "Failed to submit DataPro verification",
            "response": submit_response
        }

    # 2. Call Trace API
    trace_submit_status, trace_submit_response = submit_trace_request(identity_number, reference)

    if trace_submit_status in [200, 303]:
        trace_request_id = trace_submit_response.get('request_id')
        if trace_request_id:
            time.sleep(2)
            trace_status, trace_results = get_trace_results(trace_request_id)
            extracted = extract_trace_data(trace_results)
            combined_results["trace"] = {
                "success": trace_status in [200, 227],
                "status_code": trace_status,
                "request_id": trace_request_id,
                "data": trace_results,
                "extracted": extracted
            }
        else:
            combined_results["trace"] = {
                "success": False,
                "status_code": trace_submit_status,
                "error": "No request_id received",
                "response": trace_submit_response
            }
    else:
        combined_results["trace"] = {
            "success": False,
            "status_code": trace_submit_status,
            "error": "Failed to submit trace request",
            "response": trace_submit_response
        }

    # 3. Call AML Risk Search API - uses the name/DOB matched by DataPro above,
    # so the client only ever has to submit an identity_number for the whole run.
    aml_first_name = None
    aml_middle_name = None
    aml_surname = None
    aml_dob = None

    datapro_block = combined_results["datapro"]
    if datapro_block.get("success"):
        dp_response_list = datapro_block.get("data", {}).get("response", [])
        if dp_response_list:
            dha = dp_response_list[0]
            full_first_names = dha.get("first_names")
            if full_first_names:
                name_parts = full_first_names.strip().split(" ", 1)
                aml_first_name = name_parts[0]
                if len(name_parts) > 1:
                    aml_middle_name = name_parts[1]
            aml_surname = dha.get("last_name")
            aml_dob = dha.get("date_of_birth")

    if aml_first_name and aml_surname:
        aml_submit_status, aml_submit_response = submit_aml_verification(
            aml_first_name, aml_surname,
            middle_name=aml_middle_name,
            date_of_birth=aml_dob,
            country="South Africa",
            reference=reference
        )

        if aml_submit_status in [200, 303]:
            aml_request_id = aml_submit_response.get('request_id')
            if aml_request_id:
                time.sleep(2)
                aml_status, aml_results = get_aml_results(aml_request_id)
                combined_results["aml"] = {
                    "success": aml_status in [200, 206, 227],
                    "status_code": aml_status,
                    "request_id": aml_request_id,
                    "data": aml_results
                }
            else:
                combined_results["aml"] = {
                    "success": False,
                    "status_code": aml_submit_status,
                    "error": "No request_id received",
                    "response": aml_submit_response
                }
        else:
            combined_results["aml"] = {
                "success": False,
                "status_code": aml_submit_status,
                "error": "Failed to submit AML risk search",
                "response": aml_submit_response
            }
    else:
        combined_results["aml"] = {
            "success": False,
            "error": "Insufficient name data from DataPro match to run AML search"
        }

    # Determine overall success
    overall_success = (
        combined_results["datapro"].get("success", False) or
        combined_results["trace"].get("success", False) or
        combined_results["aml"].get("success", False)
    )

    return jsonify({
        "success": overall_success,
        "results": combined_results
    })

@app.route('/check/datapro/<request_id>', methods=['GET'])
def check_datapro_request(request_id):
    """Check status of DataPro request"""

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    result_status, results = get_datapro_results(request_id, max_attempts=1)

    return jsonify({
        "success": result_status in [200, 206, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/check/trace/<request_id>', methods=['GET'])
def check_trace_request(request_id):
    """Check status of Trace request"""

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    result_status, results = get_trace_results(request_id, max_attempts=1)
    extracted = extract_trace_data(results)

    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results,
        "extracted": extracted
    })

@app.route('/aml', methods=['POST'])
def aml_search():
    """AML Risk Search only - individual sanctions/PEP/adverse-media screening"""

    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400

    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400

    first_name = data.get('first_name')
    surname = data.get('surname')
    middle_name = data.get('middle_name')
    date_of_birth = data.get('date_of_birth')
    country = data.get('country')
    reference = data.get('reference', '')

    if not first_name or not surname:
        return jsonify({
            "success": False,
            "error": "first_name and surname are required"
        }), 400

    submit_status, submit_response = submit_aml_verification(
        first_name, surname,
        middle_name=middle_name,
        date_of_birth=date_of_birth,
        country=country,
        reference=reference
    )

    if submit_status != 303 and submit_status != 200:
        return jsonify({
            "success": False,
            "error": "Failed to submit AML risk search",
            "status_code": submit_status,
            "response": submit_response
        }), submit_status

    request_id = submit_response.get('request_id')

    if not request_id:
        return jsonify({
            "success": False,
            "error": "No request_id received",
            "response": submit_response
        }), 500

    time.sleep(2)

    result_status, results = get_aml_results(request_id)

    return jsonify({
        "success": result_status in [200, 206, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/download-attachment', methods=['POST'])
def download_attachment():
    """Proxy-download a ThisIsMe attachment (report PDF / photo) using the
    mTLS client cert, since Deluge can't present a client certificate itself."""

    if not verify_api_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
    except:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    file_url = data.get('url')
    filename = data.get('filename') or 'attachment'

    if not file_url:
        return jsonify({"success": False, "error": "url is required"}), 400

    if not file_url.startswith(BASE_URL):
        return jsonify({"success": False, "error": "url must be a ThisIsMe attachment link"}), 400

    try:
        resp = requests.get(
            file_url,
            verify=False,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "type": type(e).__name__}), 500

    if resp.status_code != 200:
        return jsonify({
            "success": False,
            "error": "Failed to download attachment",
            "status_code": resp.status_code
        }), resp.status_code

    content_type = resp.headers.get('Content-Type', 'application/octet-stream')

    return Response(
        resp.content,
        mimetype=content_type,
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
