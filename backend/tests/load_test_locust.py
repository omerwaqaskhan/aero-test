"""
Load testing script using Locust for LuftWay Travel Platform.

Installation:
    pip install locust

Usage:
    locust -f backend/tests/load_test_locust.py --host=http://localhost:8000

Then open http://localhost:8089 in your browser to start the test.
"""

from locust import HttpUser, task, between
import random
from datetime import date, timedelta


class LuftWayUser(HttpUser):
    """Simulates a typical user browsing and searching for hotels."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Optional: Login if needed
        # self.client.post("/api/v1/auth/login", json={
        #     "email": "test@example.com",
        #     "password": "Test123!@#"
        # })
        pass
    
    @task(3)
    def search_hotels(self):
        """Search for hotels - most common action."""
        destinations = ["Paris", "Tokyo", "London", "New York", "Dubai", "Barcelona"]
        destination = random.choice(destinations)
        
        # Random dates 1-30 days in the future
        check_in = date.today() + timedelta(days=random.randint(1, 30))
        check_out = check_in + timedelta(days=random.randint(1, 7))
        
        params = {
            "destination": destination,
            "check_in": str(check_in),
            "check_out": str(check_out),
            "guests": random.randint(1, 4),
            "rooms": random.randint(1, 2),
            "page": random.randint(1, 5),
            "page_size": 20
        }
        
        self.client.get("/api/v1/search-booking/search", params=params, name="Search Hotels")
    
    @task(2)
    def get_hotel_details(self):
        """View hotel details."""
        # This would need actual hotel IDs from your database
        # For now, using a placeholder
        hotel_id = "a5431bc8-b1c8-4381-9ede-4aa84aeb8d25"  # Replace with actual hotel ID
        self.client.get(f"/api/v1/search-booking/hotels/{hotel_id}", name="Hotel Details")
    
    @task(1)
    def get_all_hotels(self):
        """Browse all hotels."""
        params = {
            "page": random.randint(1, 10),
            "page_size": 20
        }
        self.client.get("/api/v1/search-booking/hotels", params=params, name="All Hotels")
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="Health Check")

