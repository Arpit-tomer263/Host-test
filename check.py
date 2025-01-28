import requests

url = "https://humble-eureka-q7vv6wjwgpq6cxxxv-5000.app.github.dev/Checking"
payload = {"data": "example"}

# Optional headers if necessary
headers = {'Authorization': '75923'}

print(f"Sending headers: {headers}")  # Debugging line to print headers

response = requests.post(url, json=payload, headers=headers, verify=False)

print(f"Response code: {response.status_code}")
print(f"Response body: {response.text}")
