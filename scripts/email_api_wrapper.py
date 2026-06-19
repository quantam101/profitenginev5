#!/usr/bin/env python3
"""
Email List Manager API Wrapper
REST API endpoints for email subscriber management.
Can be integrated into ProfitEngine backend via FastAPI or similar.
"""

import json
from typing import Optional, Dict, List
import logging
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from email_list_manager import EmailListManager, SubscriberStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailAPIWrapper:
    """
    RESTful API wrapper for email list management.
    Provides endpoints for subscriber management, campaigns, and engagement tracking.
    """

    def __init__(self, db_path: str = "profitengine_subscribers.db"):
        """Initialize API wrapper with email manager"""
        self.manager = EmailListManager(db_path)

    # Subscriber Management Endpoints

    def subscribe(self, payload: Dict) -> Dict:
        """
        POST /api/email/subscribe
        Create a new subscription with double opt-in
        """
        try:
            email = payload.get('email', '').strip().lower()
            name = payload.get('name', '').strip()
            interests = payload.get('interests', [])
            segment = payload.get('segment', 'free')

            if not email or not name:
                return {
                    'success': False,
                    'error': 'Email and name are required',
                    'code': 'INVALID_INPUT'
                }

            success, message, subscriber_id = self.manager.add_subscriber(
                email, name, interests, segment
            )

            return {
                'success': success,
                'message': message,
                'subscriber_id': subscriber_id,
                'code': 'SUBSCRIBER_ADDED' if success else 'ADD_FAILED'
            }

        except Exception as e:
            logger.error(f"Subscribe error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def confirm_subscription(self, payload: Dict) -> Dict:
        """
        POST /api/email/confirm
        Confirm double opt-in subscription
        """
        try:
            token = payload.get('token', '')

            if not token:
                return {
                    'success': False,
                    'error': 'Confirmation token is required',
                    'code': 'INVALID_INPUT'
                }

            success, message = self.manager.confirm_subscription(token)

            return {
                'success': success,
                'message': message,
                'code': 'CONFIRMED' if success else 'CONFIRMATION_FAILED'
            }

        except Exception as e:
            logger.error(f"Confirmation error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def unsubscribe(self, payload: Dict) -> Dict:
        """
        POST /api/email/unsubscribe
        Unsubscribe via token (email footer link)
        """
        try:
            token = payload.get('token', '')

            if not token:
                return {
                    'success': False,
                    'error': 'Unsubscribe token is required',
                    'code': 'INVALID_INPUT'
                }

            success, message = self.manager.unsubscribe(token)

            return {
                'success': success,
                'message': message,
                'code': 'UNSUBSCRIBED' if success else 'UNSUBSCRIBE_FAILED'
            }

        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def get_subscriber(self, email: str) -> Dict:
        """
        GET /api/email/subscribers/{email}
        Retrieve subscriber details
        """
        try:
            subscriber = self.manager.get_subscriber_by_email(email)

            if not subscriber:
                return {
                    'success': False,
                    'error': 'Subscriber not found',
                    'code': 'NOT_FOUND'
                }

            return {
                'success': True,
                'data': {
                    'email': subscriber['email'],
                    'name': subscriber['name'],
                    'status': subscriber['status'],
                    'segment': subscriber['segment'],
                    'open_count': subscriber['open_count'],
                    'click_count': subscriber['click_count'],
                    'referral_count': subscriber['referral_count'],
                    'date_joined': subscriber['date_joined'],
                    'last_engagement': subscriber['last_engagement']
                },
                'code': 'SUBSCRIBER_FOUND'
            }

        except Exception as e:
            logger.error(f"Get subscriber error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def update_preferences(self, email: str, payload: Dict) -> Dict:
        """
        PUT /api/email/preferences/{email}
        Update subscriber preferences
        """
        try:
            subscriber = self.manager.get_subscriber_by_email(email)
            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found', 'code': 'NOT_FOUND'}

            success, message = self.manager.update_preferences(
                subscriber['subscriber_id'],
                email_frequency=payload.get('email_frequency'),
                newsletter=payload.get('newsletter'),
                product_updates=payload.get('product_updates'),
                promotions=payload.get('promotions'),
                account_notifications=payload.get('account_notifications')
            )

            return {
                'success': success,
                'message': message,
                'code': 'PREFERENCES_UPDATED' if success else 'UPDATE_FAILED'
            }

        except Exception as e:
            logger.error(f"Update preferences error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def pause_subscription(self, email: str) -> Dict:
        """
        POST /api/email/pause/{email}
        Temporarily pause a subscription
        """
        try:
            subscriber = self.manager.get_subscriber_by_email(email)
            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found', 'code': 'NOT_FOUND'}

            success, message = self.manager.pause_subscription(subscriber['subscriber_id'])

            return {
                'success': success,
                'message': message,
                'code': 'PAUSED' if success else 'PAUSE_FAILED'
            }

        except Exception as e:
            logger.error(f"Pause subscription error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def resume_subscription(self, email: str) -> Dict:
        """
        POST /api/email/resume/{email}
        Resume a paused subscription
        """
        try:
            subscriber = self.manager.get_subscriber_by_email(email)
            if not subscriber:
                return {'success': False, 'error': 'Subscriber not found', 'code': 'NOT_FOUND'}

            success, message = self.manager.resume_subscription(subscriber['subscriber_id'])

            return {
                'success': success,
                'message': message,
                'code': 'RESUMED' if success else 'RESUME_FAILED'
            }

        except Exception as e:
            logger.error(f"Resume subscription error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Engagement Tracking Endpoints

    def track_open(self, payload: Dict) -> Dict:
        """
        POST /api/email/track/open
        Track email open event (pixel tracking)
        """
        try:
            email = payload.get('email', '').strip().lower()
            campaign_id = payload.get('campaign_id', '')

            if not email or not campaign_id:
                return {
                    'success': False,
                    'error': 'Email and campaign_id are required',
                    'code': 'INVALID_INPUT'
                }

            success, message = self.manager.track_open(
                email,
                campaign_id,
                user_agent=payload.get('user_agent', ''),
                ip_address=payload.get('ip_address', '')
            )

            return {
                'success': success,
                'message': message,
                'code': 'OPEN_TRACKED' if success else 'TRACK_FAILED'
            }

        except Exception as e:
            logger.error(f"Track open error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def track_click(self, payload: Dict) -> Dict:
        """
        POST /api/email/track/click
        Track email click event
        """
        try:
            email = payload.get('email', '').strip().lower()
            campaign_id = payload.get('campaign_id', '')
            link_url = payload.get('link_url', '')

            if not email or not campaign_id or not link_url:
                return {
                    'success': False,
                    'error': 'Email, campaign_id, and link_url are required',
                    'code': 'INVALID_INPUT'
                }

            success, message = self.manager.track_click(
                email,
                campaign_id,
                link_url,
                user_agent=payload.get('user_agent', ''),
                ip_address=payload.get('ip_address', '')
            )

            return {
                'success': success,
                'message': message,
                'code': 'CLICK_TRACKED' if success else 'TRACK_FAILED'
            }

        except Exception as e:
            logger.error(f"Track click error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Campaign Management Endpoints

    def create_campaign(self, payload: Dict) -> Dict:
        """
        POST /api/email/campaigns
        Create an email campaign
        """
        try:
            name = payload.get('name', '').strip()
            subject = payload.get('subject', '').strip()
            segment_id = payload.get('segment_id')

            if not name or not subject:
                return {
                    'success': False,
                    'error': 'Campaign name and subject are required',
                    'code': 'INVALID_INPUT'
                }

            success, message, campaign_id = self.manager.create_campaign(
                name, subject, segment_id
            )

            return {
                'success': success,
                'message': message,
                'campaign_id': campaign_id,
                'code': 'CAMPAIGN_CREATED' if success else 'CREATE_FAILED'
            }

        except Exception as e:
            logger.error(f"Create campaign error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """
        GET /api/email/campaigns/{campaign_id}/stats
        Get campaign engagement statistics
        """
        try:
            stats = self.manager.get_campaign_stats(campaign_id)

            if not stats:
                return {
                    'success': False,
                    'error': 'Campaign not found',
                    'code': 'NOT_FOUND'
                }

            return {
                'success': True,
                'data': stats,
                'code': 'STATS_RETRIEVED'
            }

        except Exception as e:
            logger.error(f"Get campaign stats error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Segment Management Endpoints

    def create_segment(self, payload: Dict) -> Dict:
        """
        POST /api/email/segments
        Create a subscriber segment
        """
        try:
            name = payload.get('name', '').strip()
            segment_type = payload.get('segment_type', '').strip()
            criteria = payload.get('criteria', {})

            if not name or not segment_type:
                return {
                    'success': False,
                    'error': 'Segment name and type are required',
                    'code': 'INVALID_INPUT'
                }

            success, message, segment_id = self.manager.create_segment(
                name, segment_type, criteria
            )

            return {
                'success': success,
                'message': message,
                'segment_id': segment_id,
                'code': 'SEGMENT_CREATED' if success else 'CREATE_FAILED'
            }

        except Exception as e:
            logger.error(f"Create segment error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def get_active_subscribers(self, segment: Optional[str] = None, limit: int = 1000) -> Dict:
        """
        GET /api/email/subscribers?segment=free&limit=100
        Get active subscribers, optionally filtered by segment
        """
        try:
            subscribers = self.manager.get_active_subscribers(segment, limit)

            return {
                'success': True,
                'data': subscribers,
                'count': len(subscribers),
                'code': 'SUBSCRIBERS_RETRIEVED'
            }

        except Exception as e:
            logger.error(f"Get subscribers error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Lead Magnet Endpoints

    def add_lead_magnet(self, payload: Dict) -> Dict:
        """
        POST /api/email/lead-magnets
        Add a free lead magnet (ebook, template, etc.)
        """
        try:
            name = payload.get('name', '').strip()
            description = payload.get('description', '').strip()
            file_url = payload.get('file_url', '').strip()

            if not name or not file_url:
                return {
                    'success': False,
                    'error': 'Lead magnet name and file_url are required',
                    'code': 'INVALID_INPUT'
                }

            success, message, magnet_id = self.manager.add_lead_magnet(
                name, description, file_url
            )

            return {
                'success': success,
                'message': message,
                'lead_magnet_id': magnet_id,
                'code': 'MAGNET_ADDED' if success else 'ADD_FAILED'
            }

        except Exception as e:
            logger.error(f"Add lead magnet error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def track_magnet_download(self, payload: Dict) -> Dict:
        """
        POST /api/email/lead-magnets/download
        Track lead magnet download
        """
        try:
            lead_magnet_id = payload.get('lead_magnet_id', '')
            email = payload.get('email', '').strip().lower() if payload.get('email') else None
            subscriber_id = payload.get('subscriber_id')

            if not lead_magnet_id or (not email and not subscriber_id):
                return {
                    'success': False,
                    'error': 'lead_magnet_id and either email or subscriber_id are required',
                    'code': 'INVALID_INPUT'
                }

            success, message = self.manager.track_magnet_download(
                lead_magnet_id, email, subscriber_id
            )

            return {
                'success': success,
                'message': message,
                'code': 'DOWNLOAD_TRACKED' if success else 'TRACK_FAILED'
            }

        except Exception as e:
            logger.error(f"Track magnet download error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Referral Endpoints

    def create_referral(self, payload: Dict) -> Dict:
        """
        POST /api/email/referrals
        Create a referral link for growth automation
        """
        try:
            referrer_id = payload.get('referrer_id', '')
            referred_email = payload.get('referred_email', '').strip().lower()

            if not referrer_id or not referred_email:
                return {
                    'success': False,
                    'error': 'referrer_id and referred_email are required',
                    'code': 'INVALID_INPUT'
                }

            success, message, referral_token = self.manager.create_referral(
                referrer_id, referred_email
            )

            return {
                'success': success,
                'message': message,
                'referral_token': referral_token,
                'code': 'REFERRAL_CREATED' if success else 'CREATE_FAILED'
            }

        except Exception as e:
            logger.error(f"Create referral error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    # Analytics Endpoints

    def get_metrics(self) -> Dict:
        """
        GET /api/email/metrics
        Get overall engagement metrics
        """
        try:
            metrics = self.manager.get_engagement_metrics()

            return {
                'success': True,
                'data': metrics,
                'code': 'METRICS_RETRIEVED'
            }

        except Exception as e:
            logger.error(f"Get metrics error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}

    def export_subscribers(self, segment: Optional[str] = None, format: str = 'json') -> Dict:
        """
        GET /api/email/export?segment=free&format=json
        Export subscribers to JSON or CSV for email service integration
        """
        try:
            if format not in ['json', 'csv']:
                return {
                    'success': False,
                    'error': 'Format must be json or csv',
                    'code': 'INVALID_INPUT'
                }

            export_data = self.manager.export_subscribers(segment, format)

            if not export_data:
                return {
                    'success': False,
                    'error': 'No subscribers to export',
                    'code': 'NO_DATA'
                }

            return {
                'success': True,
                'data': export_data,
                'format': format,
                'code': 'EXPORT_COMPLETE'
            }

        except Exception as e:
            logger.error(f"Export error: {e}")
            return {'success': False, 'error': str(e), 'code': 'SERVER_ERROR'}


# FastAPI integration example
def create_fastapi_routes(api: EmailAPIWrapper):
    """
    Example FastAPI route definitions using the EmailAPIWrapper.
    Copy this pattern into your FastAPI app.
    """
    routes_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI(title="Email List Manager API")
email_api = EmailAPIWrapper()

# Request models
class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str
    interests: Optional[List[str]] = []
    segment: str = "free"

class ConfirmRequest(BaseModel):
    token: str

class TrackOpenRequest(BaseModel):
    email: EmailStr
    campaign_id: str
    user_agent: Optional[str] = ""
    ip_address: Optional[str] = ""

class TrackClickRequest(BaseModel):
    email: EmailStr
    campaign_id: str
    link_url: str
    user_agent: Optional[str] = ""
    ip_address: Optional[str] = ""

# Subscriber endpoints
@app.post("/api/email/subscribe")
async def subscribe(request: SubscribeRequest):
    return email_api.subscribe(request.dict())

@app.post("/api/email/confirm")
async def confirm(request: ConfirmRequest):
    return email_api.confirm_subscription(request.dict())

@app.post("/api/email/unsubscribe/{token}")
async def unsubscribe(token: str):
    return email_api.unsubscribe({"token": token})

@app.get("/api/email/subscribers/{email}")
async def get_subscriber(email: str):
    return email_api.get_subscriber(email)

# Engagement tracking
@app.post("/api/email/track/open")
async def track_open(request: TrackOpenRequest):
    return email_api.track_open(request.dict())

@app.post("/api/email/track/click")
async def track_click(request: TrackClickRequest):
    return email_api.track_click(request.dict())

# Metrics
@app.get("/api/email/metrics")
async def get_metrics():
    return email_api.get_metrics()

@app.get("/api/email/export")
async def export_subscribers(segment: Optional[str] = None, format: str = "json"):
    return email_api.export_subscribers(segment, format)
    '''
    return routes_code


if __name__ == "__main__":
    api = EmailAPIWrapper()
    print("Email API Wrapper initialized")
    print("\nAvailable API Methods:")
    for method in dir(api):
        if not method.startswith('_'):
            print(f"  - {method}()")
