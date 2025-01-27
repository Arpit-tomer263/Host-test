import requests
import json
from datetime import datetime

# The URL of your webhook
server_url = 'http://127.0.0.1:5000/webhook'
pair = "EURUSD"
signalType = "Buy"
entryPrice = 1.2350
takeProfit = 1.2380
stopLoss = 1.2300
lossComment = "Take profit reached"
# Call handleTradeClosure function to generate the message
message = {
    "Pair": pair,
    "Type": "Entry Long",
    "Signal": signalType,
    "Date/time": "2025-01-26 10:15:00",
    "Price USD": entryPrice,
    "Contracts": 10,
    "Profit": 50,
    "Profit %": 0.4,
    "Run-up": 0.0025,
    "Run-up %": 0.2,
    "Drawdown": 0.0015,
    "Drawdown %": 0.1,
    "Risk": 0.0010,
    "Reward": 0.0020,
    "TimeFrame": "1",
    "Comment": lossComment
}

# Send the request with the data
try:
    response = requests.post(server_url, json=message)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
except Exception as e:
    print(f"An error occurred: {e}")
