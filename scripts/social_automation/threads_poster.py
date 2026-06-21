#!/usr/bin/env python3
"""
Threads poster - posts directly to Threads via Meta Graph API
More direct engagement with minimal algorithm interference
"""

import os
import requests
import json
from datetime import datetime

THREADS_TOKEN = os.getenv('THREADS_ACCESS_TOKEN')
THREADS_USER_ID = os.getenv('THREADS_USER_ID')
THREADS_API_VERSION = 'v18.0'

def post_thread(text: str, image_url: str = None):
    """Post to Threads"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{THREADS_USER_ID}/threads"

    payload = {
        'text': text,
        'access_token': THREADS_TOKEN
    }

    if image_url:
        payload['image_url'] = image_url

    response = requests.post(endpoint, json=payload, timeout=10)

    if response.status_code == 200:
        thread_id = response.json()['id']
        print(f"✓ Thread posted: {thread_id}")

        # Publish the thread
        publish_endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/publish"
        publish_response = requests.post(publish_endpoint, json={'access_token': THREADS_TOKEN}, timeout=10)

        if publish_response.status_code == 200:
            print(f"✓ Thread published!")
            return thread_id

    print(f"✗ Error: {response.text}")
    return None

def reply_to_thread(thread_id: str, text: str):
    """Reply to a thread"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/replies"

    payload = {
        'text': text,
        'access_token': THREADS_TOKEN
    }

    response = requests.post(endpoint, json=payload, timeout=10)

    if response.status_code == 200:
        print(f"✓ Reply posted")
        return response.json()['id']

    print(f"✗ Error: {response.text}")
    return None

def get_thread_insights(thread_id: str):
    """Get thread engagement metrics"""

    endpoint = f"https://graph.threads.net/{THREADS_API_VERSION}/{thread_id}/insights"

    params = {
        'metric': 'likes,replies,reposts,quotes',
        'access_token': THREADS_TOKEN
    }

    response = requests.get(endpoint, params=params, timeout=10)

    if response.status_code == 200:
        insights = response.json()['data']
        print(f"\n[Thread {thread_id} Insights]")
        for metric in insights:
            print(f"  {metric['title']}: {metric['values'][0]['value']}")
    else:
        print(f"✗ Error: {response.text}")

if __name__ == '__main__':
    print("Threads posting automation ready")
    print(f"User ID: {THREADS_USER_ID}")

    # Example usage:
    # post_thread("Here's my latest AI productivity insight...")
