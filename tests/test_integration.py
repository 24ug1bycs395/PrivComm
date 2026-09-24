import sys
import os
sys.path.insert(0, os.path.abspath("."))
from fastapi.testclient import TestClient
from main import app

def run_tests():
    client = TestClient(app)

    print("--- 1. Testing Health Endpoint ---")
    res = client.get("/health")
    assert res.status_code == 200
    print("Health response:", res.json())

    print("\n--- 2. Testing Testbed Scenarios ---")
    res = client.get("/api/testbed/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    print(f"Loaded {len(scenarios)} testbed scenarios:")
    for s in scenarios:
        print(f"  - [{s['id']}] {s['name']}")

    print("\n--- 3. Testing Sample Analysis ---")
    res = client.get("/analyze/sample")
    assert res.status_code == 200
    sample_data = res.json()
    print("IPsec Detected:", sample_data.get("ipsec_detected"))
    print("IKE Version:", sample_data.get("ike_version"))
    print("Traffic Class:", sample_data.get("traffic_classification", {}).get("traffic_type"))
    print("Risk Level:", sample_data.get("security_assessment", {}).get("risk_level"))

    print("\n--- 4. Testing Analysis Jobs Vault ---")
    res = client.get("/api/jobs")
    assert res.status_code == 200
    jobs = res.json()
    print(f"Jobs in database: {len(jobs)}")

    print("\n--- 5. Testing Testbed Launch ---")
    res = client.post("/api/testbed/run", json={"scenario_id": "ikev2-aes-gcm-compliant"})
    assert res.status_code == 200
    run_res = res.json()
    print("Testbed launch:", run_res)
    job_id = run_res["job_id"]

    print("\n--- 6. Testing Testbed Job Polling ---")
    res = client.get(f"/api/testbed/jobs/{job_id}")
    assert res.status_code == 200
    print("Job status:", res.json()["state"])

    print("\n==========================================")
    print(" ALL BACKEND INTEGRATION TESTS PASSED! ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
