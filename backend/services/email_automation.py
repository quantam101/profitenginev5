"""
Email Automation using free Resend tier

Free tier: 100 emails/day
Automation:
- Welcome sequences
- Product recommendations
- Revenue updates
- Content distribution
"""
import os

try:
    from resend import Resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    Resend = None

class EmailAutomation:
    """Send automated emails via Resend free tier."""

    def __init__(self):
        if RESEND_AVAILABLE:
            self.resend = Resend(api_key=os.getenv("RESEND_API_KEY"))
        else:
            self.resend = None

    async def send_welcome_sequence(self, email: str, name: str):
        """Send welcome email sequence."""

        emails = [
            {
                "to": email,
                "subject": "Welcome to ProfitEngine!",
                "html": f"<h1>Welcome {name}!</h1><p>Start earning passive income with our complete revenue system.</p>"
            },
            {
                "to": email,
                "subject": "Your First Digital Product is Ready",
                "html": "<p>Check out our POD Listings 8-Pack...</p>"
            },
            {
                "to": email,
                "subject": "$500/Month Revenue Case Study",
                "html": "<p>See how creators are making $500-5000/month...</p>"
            }
        ]

        for email_payload in emails:
            await self.resend.emails.send(email_payload)

    async def send_revenue_update(self, email: str, revenue: float):
        """Send revenue update email."""

        await self.resend.emails.send({
            "to": email,
            "subject": f"💰 You earned ${revenue:.2f}!",
            "html": f"<h2>Revenue Update</h2><p>Your systems generated ${revenue:.2f} today.</p>"
        })

