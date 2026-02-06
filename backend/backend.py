import requests
import json

# wger API import
import requests

url = "https://wger.de/en/software/api"
headers = {
    "Content-Type": "application/json"
}

response = requests.get(url)
data = response.json()
print(data)