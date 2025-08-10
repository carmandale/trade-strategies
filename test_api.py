"""Simple manual check script for current endpoints (non-test)."""
import requests

BASE = "http://localhost:8000"

print("GET /health")
print(requests.get(f"{BASE}/health").json())

print("GET /current_price/SPY")
print(requests.get(f"{BASE}/current_price/SPY").json())