import requests

# Flask server URL
url = "http://localhost:5000/Checking"

# Send data to the Flask server (can be empty or include whatever data you want)
payload = {"data": "example"}  # Example data to send, can be an empty JSON

# POST request to /Checking
response = requests.post(url, json=payload)

# Print the response from the server
if response.status_code == 200:
    response_data = response.json()
    print(f"Server response: {response_data['message']}")
else:
    print(f"Failed to get response. Status code: {response.status_code}")
