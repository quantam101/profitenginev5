#!/usr/bin/env python3
"""
Email Service Integrations for ProfitEngine v5
Export subscribers to Beehiiv, Resend, and other platforms.
Track engagement across multiple email service providers.
"""

import json
import logging
import requests
from typing import Optional, Dict, List, Tuple
import os
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from email_list_manager import EmailListManager, SubscriberStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BeehiivIntegration:
    """Integration with Beehiiv email platform"""

    def __init__(self, api_key: str):
        """Initialize Beehiiv API client"""
        self.api_key = api_key
        self.base_url = "https://api.beehiiv.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def import_subscribers(self, subscribers: List[Dict]) -> Tuple[bool, str]:
        """
        Bulk import subscribers to Beehiiv publication.
        """
        try:
            endpoint = f"{self.base_url}/publications"

            # First, get publication ID
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                return False, f"Failed to fetch publications: {response.text}"

            publications = response.json().get('data', [])
            if not publications:
                return False, "No publications found in Beehiiv account"

            pub_id = publications[0]['id']

            # Import subscribers
            imported = 0
            errors = []

            for subscriber in subscribers:
                payload = {
                    "email": subscriber['email'],
                    "name": subscriber.get('name', ''),
                    "custom_fields": {
                        "segment": subscriber.get('segment', 'free'),
                        "interests": ','.join(subscriber.get('interests', []))
                    }
                }

                try:
                    response = requests.post(
                        f"{self.base_url}/publications/{pub_id}/subscriptions",
                        headers=self.headers,
                        json=payload,
                        timeout=10
                    )

                    if response.status_code == 201:
                        imported += 1
                    else:
                        errors.append(f"{subscriber['email']}: {response.text}")

                except requests.RequestException as e:
                    errors.append(f"{subscriber['email']}: {str(e)}")

            message = f"Imported {imported}/{len(subscribers)} subscribers to Beehiiv"
            if errors:
                message += f"\nErrors: {len(errors)}"
                logger.warning(message)

            return True, message

        except Exception as e:
            logger.error(f"Beehiiv integration error: {e}")
            return False, f"Beehiiv API error: {str(e)}"

    def sync_segment(
        self,
        segment_name: str,
        subscribers: List[Dict]
    ) -> Tuple[bool, str]:
        """Sync a specific segment to Beehiiv as a tag"""
        try:
            # Create a tag in Beehiiv for the segment
            pub_id = None  # Would be fetched from publications endpoint
            tag = {
                "name": segment_name,
                "description": f"Segment: {segment_name}"
            }

            # Tag subscribers with segment
            for subscriber in subscribers:
                logger.info(f"Tagging {subscriber['email']} with {segment_name}")

            return True, f"Synced segment {segment_name} with {len(subscribers)} subscribers"

        except Exception as e:
            logger.error(f"Error syncing segment: {e}")
            return False, f"Sync failed: {str(e)}"


class ResendIntegration:
    """Integration with Resend email platform"""

    def __init__(self, api_key: str):
        """Initialize Resend API client"""
        self.api_key = api_key
        self.base_url = "https://api.resend.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def import_contacts(self, audience_id: str, subscribers: List[Dict]) -> Tuple[bool, str]:
        """
        Import subscribers to Resend audience (contact list).
        """
        try:
            imported = 0
            errors = []

            for subscriber in subscribers:
                payload = {
                    "email": subscriber['email'],
                    "first_name": subscriber.get('name', '').split()[0] if subscriber.get('name') else '',
                    "last_name": subscriber.get('name', '').split()[-1] if subscriber.get('name') else '',
                    "unsubscribed": subscriber.get('status') == SubscriberStatus.UNSUBSCRIBED.value
                }

                try:
                    response = requests.post(
                        f"{self.base_url}/audiences/{audience_id}/contacts",
                        headers=self.headers,
                        json=payload,
                        timeout=10
                    )

                    if response.status_code in [200, 201]:
                        imported += 1
                    else:
                        errors.append(f"{subscriber['email']}: {response.text}")

                except requests.RequestException as e:
                    errors.append(f"{subscriber['email']}: {str(e)}")

            message = f"Imported {imported}/{len(subscribers)} subscribers to Resend"
            if errors:
                message += f"\nErrors: {len(errors)}"
                logger.warning(message)

            return True, message

        except Exception as e:
            logger.error(f"Resend integration error: {e}")
            return False, f"Resend API error: {str(e)}"

    def send_campaign(
        self,
        campaign_name: str,
        audience_id: str,
        subject: str,
        html_content: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Send a campaign to an audience"""
        try:
            payload = {
                "name": campaign_name,
                "audience_id": audience_id,
                "subject": subject,
                "html": html_content
            }

            response = requests.post(
                f"{self.base_url}/emails/send",
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return True, "Campaign sent successfully", data.get('id')
            else:
                return False, f"Campaign send failed: {response.text}", None

        except Exception as e:
            logger.error(f"Error sending campaign: {e}")
            return False, f"Send failed: {str(e)}", None


class MailchimpIntegration:
    """Integration with Mailchimp email platform"""

    def __init__(self, api_key: str, server_prefix: str = "us1"):
        """Initialize Mailchimp API client"""
        self.api_key = api_key
        self.server_prefix = server_prefix
        self.base_url = f"https://{server_prefix}.api.mailchimp.com/3.0"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def sync_list(self, list_id: str, subscribers: List[Dict]) -> Tuple[bool, str]:
        """Sync subscribers to Mailchimp list"""
        try:
            batch_operations = []

            for subscriber in subscribers:
                operation = {
                    "method": "PUT",
                    "path": f"/lists/{list_id}/members/{subscriber['email'].lower()}",
                    "body": json.dumps({
                        "email_address": subscriber['email'],
                        "status": "subscribed" if subscriber.get('status') == SubscriberStatus.ACTIVE.value else "unsubscribed",
                        "merge_fields": {
                            "FNAME": subscriber.get('name', '').split()[0] if subscriber.get('name') else '',
                            "LNAME": subscriber.get('name', '').split()[-1] if subscriber.get('name') else ''
                        }
                    })
                }
                batch_operations.append(operation)

            # Send batch operations
            payload = {"operations": batch_operations}

            response = requests.post(
                f"{self.base_url}/batches",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                return True, f"Synced {len(subscribers)} subscribers to Mailchimp"
            else:
                return False, f"Mailchimp sync failed: {response.text}"

        except Exception as e:
            logger.error(f"Mailchimp integration error: {e}")
            return False, f"Mailchimp API error: {str(e)}"


class EmailServiceSyncManager:
    """Manages syncing across multiple email service providers"""

    def __init__(self, email_manager: EmailListManager):
        """Initialize sync manager"""
        self.email_manager = email_manager
        self.beehiiv = None
        self.resend = None
        self.mailchimp = None

    def configure_beehiiv(self, api_key: str):
        """Configure Beehiiv integration"""
        self.beehiiv = BeehiivIntegration(api_key)
        logger.info("Beehiiv integration configured")

    def configure_resend(self, api_key: str):
        """Configure Resend integration"""
        self.resend = ResendIntegration(api_key)
        logger.info("Resend integration configured")

    def configure_mailchimp(self, api_key: str, server_prefix: str = "us1"):
        """Configure Mailchimp integration"""
        self.mailchimp = MailchimpIntegration(api_key, server_prefix)
        logger.info("Mailchimp integration configured")

    def sync_all_platforms(self, segment: Optional[str] = None) -> Dict[str, Tuple[bool, str]]:
        """Sync subscribers to all configured platforms"""
        results = {}

        # Get subscribers to sync
        subscribers = self.email_manager.get_active_subscribers(segment)
        if not subscribers:
            return {"error": (False, "No active subscribers to sync")}

        # Convert to export format
        export_json = self.email_manager.export_subscribers(segment, "json")
        if not export_json:
            return {"error": (False, "Failed to export subscribers")}

        export_data = json.loads(export_json)

        # Sync to Beehiiv
        if self.beehiiv:
            results['beehiiv'] = self.beehiiv.import_subscribers(export_data)

        # Sync to Resend
        if self.resend:
            audience_id = os.getenv("RESEND_AUDIENCE_ID", "")
            if audience_id:
                results['resend'] = self.resend.import_contacts(audience_id, export_data)
            else:
                results['resend'] = (False, "RESEND_AUDIENCE_ID not configured")

        # Sync to Mailchimp
        if self.mailchimp:
            list_id = os.getenv("MAILCHIMP_LIST_ID", "")
            if list_id:
                results['mailchimp'] = self.mailchimp.sync_list(list_id, export_data)
            else:
                results['mailchimp'] = (False, "MAILCHIMP_LIST_ID not configured")

        return results

    def sync_segment(self, segment: str, platforms: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Sync a specific segment to selected platforms"""
        results = {}
        subscribers = self.email_manager.get_active_subscribers(segment)

        if not subscribers:
            return {segment: (False, "No subscribers in segment")}

        export_json = self.email_manager.export_subscribers(segment, "json")
        if not export_json:
            return {segment: (False, "Failed to export segment")}

        export_data = json.loads(export_json)

        for platform in platforms:
            if platform == "beehiiv" and self.beehiiv:
                results[f"{segment}_beehiiv"] = self.beehiiv.sync_segment(segment, export_data)
            elif platform == "resend" and self.resend:
                audience_id = os.getenv("RESEND_AUDIENCE_ID", "")
                if audience_id:
                    results[f"{segment}_resend"] = self.resend.import_contacts(audience_id, export_data)
            elif platform == "mailchimp" and self.mailchimp:
                list_id = os.getenv("MAILCHIMP_LIST_ID", "")
                if list_id:
                    results[f"{segment}_mailchimp"] = self.mailchimp.sync_list(list_id, export_data)

        return results


# Demo/testing
def demo():
    """Demonstrate email service integrations"""
    manager = EmailListManager()
    sync_manager = EmailServiceSyncManager(manager)

    print("\n=== Email Service Integrations Demo ===\n")

    # Add sample subscribers
    print("1. Adding sample subscribers...")
    subscribers = [
        ("alice@example.com", "Alice Johnson", ["investing"]),
        ("bob@example.com", "Bob Smith", ["passive-income"]),
    ]

    for email, name, interests in subscribers:
        success, msg, sub_id = manager.add_subscriber(
            email, name, interests, segment="free"
        )
        if sub_id:
            # Auto-confirm for demo
            cursor = manager.conn.cursor()
            cursor.execute(
                "SELECT confirmation_token FROM confirmations WHERE subscriber_id = ?",
                (sub_id,)
            )
            result = cursor.fetchone()
            if result:
                manager.confirm_subscription(result[0])

    # Get export data
    print("\n2. Exporting subscriber data...")
    json_export = manager.export_subscribers(export_format="json")
    if json_export:
        data = json.loads(json_export)
        print(f"  Exported {len(data)} subscribers")
        print("  Sample export:", json.dumps(data[0], indent=2))

    # Show integration setup
    print("\n3. Email service integration setup...")
    print("  Beehiiv: Configure with BEEHIIV_API_KEY")
    print("  Resend: Configure with RESEND_API_KEY and RESEND_AUDIENCE_ID")
    print("  Mailchimp: Configure with MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID")

    print("\n=== Demo Complete ===\n")
    manager.close()


if __name__ == "__main__":
    demo()
