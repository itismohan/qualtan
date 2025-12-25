import os
from locust import HttpUser, task, between

class ApiPerformanceUser(HttpUser):
    wait_time = between(1, 5)
    
    @task(3)
    def test_rest_api(self):
        """Example REST API performance test."""
        self.client.get("/api/v1/resource", headers={"Authorization": "Bearer token"})

    @task(1)
    def test_graphql_api(self):
        """Example GraphQL API performance test."""
        query = """
        query {
          user(id: "1") {
            id
            username
            email
          }
        }
        """
        self.client.post("/graphql", json={"query": query})

# To run: locust -f performance/locustfile.py --host=https://api.example.com
