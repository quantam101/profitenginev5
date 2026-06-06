#!/usr/bin/env python3
import urllib.request, json, os

token = os.environ["PRINTIFY_API_TOKEN"]
req = urllib.request.Request(
    "https://api.printify.com/v1/shops.json",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "ProfitEngine/5.0"}
)
resp = urllib.request.urlopen(req, timeout=15)
shops = json.loads(resp.read())
for s in shops:
    print(f"Shop ID: {s['id']}  |  Name: {s['title']}  |  Platform: {s.get('sales_channel','')}")
