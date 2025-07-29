import requests

# Test the API directly
response = requests.post('http://localhost:8000/analyze', json={
    "date": "2025-07-29",
    "ticker": "SPY",
    "contracts": 200,
    "bull_call_strikes": [637, 640],
    "iron_condor_strikes": [633, 638, 631, 640],
    "butterfly_strikes": [637, 638, 639],
    "entry_time": "08:30:00",
    "exit_time": "14:30:00"
})

print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    data = response.json()
    print(f"Success! Current price: {data['current_price']}")
    print(f"Chart data points: {len(data['chart_data'])}")
    print(f"Results: {data['results']}")