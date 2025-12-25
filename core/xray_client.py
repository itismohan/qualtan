import os
import requests

class XRayClient:
    def __init__(self):
        self.client_id = os.getenv("XRAY_CLIENT_ID")
        self.client_secret = os.getenv("XRAY_CLIENT_SECRET")
        self.base_url = "https://xray.cloud.getxray.app/api/v2"
        self.token = self._authenticate()

    def _authenticate(self):
        """Authenticates with X-Ray Cloud."""
        if not self.client_id: return None
        url = f"{self.base_url}/authenticate"
        payload = {"client_id": self.client_id, "client_secret": self.client_secret}
        response = requests.post(url, json=payload)
        return response.text.strip('"')

    def import_test_cases(self, test_data):
        """Imports test cases into X-Ray."""
        if not self.token: return "Mock: Test cases imported to X-Ray"
        url = f"{self.base_url}/import/test/bulk"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        response = requests.post(url, json=test_data, headers=headers)
        return response.json()

    def push_results(self, results_json):
        """Pushes execution results to X-Ray."""
        if not self.token: return "Mock: Results pushed to X-Ray"
        url = f"{self.base_url}/import/execution"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        response = requests.post(url, json=results_json, headers=headers)
        return response.json()
