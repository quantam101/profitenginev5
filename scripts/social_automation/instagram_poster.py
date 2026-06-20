#!/usr/bin/env python3
"""
Instagram poster - uploads content via Meta Graph API
"""

import os
import requests
import json
from datetime import datetime

INSTAGRAM_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
INSTAGRAM_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
INSTAGRAM_API_VERSION = 'v18.0'

def upload_image_post(image_url: str, caption: str, hashtags: str = ""):
    """Upload image post to Instagram"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"

    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    payload = {
        'image_url': image_url,
        'caption': full_caption,
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.post(endpoint, json=payload)

    if response.status_code == 200:
        print(f"✓ Image post created: {response.json()['id']}")
        return response.json()['id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def upload_carousel(image_urls: list, caption: str, hashtags: str = ""):
    """Upload carousel post to Instagram"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"

    # Create carousel items
    carousel_items = []
    for idx, img_url in enumerate(image_urls):
        item_payload = {
            'image_url': img_url,
            'access_token': INSTAGRAM_TOKEN
        }
        response = requests.post(endpoint, json=item_payload)
        if response.status_code == 200:
            carousel_items.append(response.json()['id'])

    # Create carousel container
    container_endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/media"
    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    container_payload = {
        'media_type': 'CAROUSEL',
        'children': carousel_items,
        'caption': full_caption,
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.post(container_endpoint, json=container_payload)

    if response.status_code == 200:
        print(f"✓ Carousel post created: {response.json()['id']}")
        return response.json()['id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def get_insights():
    """Get engagement metrics"""

    endpoint = f"https://graph.instagram.com/{INSTAGRAM_API_VERSION}/{INSTAGRAM_ACCOUNT_ID}/insights"

    metrics = [
        'impressions',
        'reach',
        'follower_count',
        'website_clicks'
    ]

    params = {
        'metric': ','.join(metrics),
        'period': 'day',
        'access_token': INSTAGRAM_TOKEN
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        insights = response.json()['data']
        print("\n[Instagram Insights]")
        for metric in insights:
            print(f"  {metric['name']}: {metric.get('values', [{}])[0].get('value', 'N/A')}")
    else:
        print(f"✗ Error fetching insights: {response.text}")

if __name__ == '__main__':
    print("Instagram posting automation ready")
    print(f"Account ID: {INSTAGRAM_ACCOUNT_ID}")

    # Example usage:
    # upload_image_post(
    #     image_url="https://example.com/image.jpg",
    #     caption="Check out this AI productivity tip!",
    #     hashtags="#AIProductivity #Automation #Tips"
    # )
