"""Tool schemas exposed to Retell and Vapi."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Return two available service appointment slots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {"type": "string", "description": "YYYY-MM-DD date to start searching from."},
                    "service_type": {
                        "type": "string",
                        "enum": ["audit", "cabling", "drone", "hardware", "cctv", "general"],
                    },
                },
                "required": ["target_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Persist a confirmed service appointment and send SMS confirmation when Twilio is configured.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_datetime": {"type": "string"},
                    "service_type": {"type": "string"},
                    "site_address": {"type": "string"},
                    "contact_phone": {"type": "string"},
                    "contact_name": {"type": "string"},
                    "company_name": {"type": "string"},
                },
                "required": ["slot_datetime", "service_type", "site_address", "contact_phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_secure_payment_link",
            "description": "Create a Stripe Checkout link and send it by SMS. Never collect card numbers by voice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_in_cents": {"type": "integer"},
                    "billing_zip": {"type": "string"},
                    "invoice_id": {"type": "string"},
                    "phone_number": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["amount_in_cents", "billing_zip", "phone_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_live",
            "description": "Transfer the caller to a live operations line.",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    },
]

