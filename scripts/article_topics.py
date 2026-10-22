"""
Article topic rotation for the ProfitEngine daily content pipeline.

Retargeted 2026-10-22: www.alreadyherellc.com/content/ is indexed only for IT
and field-service topics (see quantam101/content _config.yml). The old
rotation mixed in passive-income, affiliate and freelancing topics that
diluted rankings for the pages that bring in Already Here LLC clients, so
every topic here is IT, low-voltage, or field-service work.

Rotation starts at today's day-of-year and skips any topic an existing post
already covers, so the duplicate-topic guard in seo_content_quality never has
to block a scheduled run. When every topic is covered, pick_topic raises:
add topics here rather than letting the pipeline repeat itself.

Usage:
    from scripts.article_topics import pick_topic
    topic = pick_topic(existing_post_names)
"""
from __future__ import annotations

import re
from datetime import date
from typing import Iterable, List, Optional

TOPICS: List[str] = [
    # Buying and contracting IT services
    "How to Find a Reliable IT Field Service Company in Phoenix AZ",
    "Managed IT Services vs Break-Fix: Which Is Right for Your Business?",
    "Commercial Network Cabling Cost Guide: What to Budget in 2026",
    "IT Support SLA Guide: What Response Times Should Your Contract Guarantee?",
    "How to Write an IT Service Contract That Protects Your Business",
    "IT Budgeting for Small Business: How Much to Spend on Technology",
    "IT Support Pricing Guide: What Is a Fair Rate for On-Site Service?",
    "What to Include in a Scope of Work for an IT Field Service Visit",
    "How to Vet a Subcontracted IT Technician Before Sending Them On-Site",
    "Smart Hands Services Explained: When a Remote IT Team Needs Someone On-Site",
    "How to Compare Quotes From Low-Voltage Cabling Contractors",
    "Questions to Ask Before Signing a Multi-Site IT Rollout Contract",

    # Networking and cabling
    "PBX vs Hosted VoIP: What Most IT Vendors Won't Tell You",
    "How to Troubleshoot a Slow Business Network Without Calling IT",
    "Patch Panel vs Direct-Run Cabling: Pros and Cons for Small Offices",
    "How to Prepare Your Office for a Network Infrastructure Upgrade",
    "Best Unmanaged vs Managed Switches for Small Business Networks",
    "How to Set Up a Guest Wi-Fi Network That Keeps Your Business Safe",
    "How to Migrate Your Business Phone System to VoIP Without Downtime",
    "Wireless Site Survey: How to Plan Wi-Fi Coverage for a Commercial Space",
    "How to Label and Test Network Cabling So Future Repairs Go Faster",
    "Network Rack and IDF Closet Cleanup: A Practical Checklist",
    "PoE Explained: Powering Cameras, Access Points and Phones Over Ethernet",
    "How to Plan Network Cabling for a Warehouse or Distribution Center",
    "Fiber Optic Basics for Business Owners: Single-Mode vs Multimode",
    "Business Internet Failover: Keeping a Site's Network Online When the ISP Goes Down",
    "How to Read a Network Cabling Certification Report",
    "Firewall Basics for Small Offices: What It Does and What It Doesn't",

    # Retail, restaurant and multi-site rollouts
    "POS System Installation Checklist for Retail and Restaurant Openings",
    "How to Plan a Multi-Site IT Rollout Across Arizona Locations",
    "Self-Service Kiosk Installation: Network, Power and Mounting Requirements",
    "Restaurant Network Setup: Separating POS, Guest Wi-Fi and Kitchen Systems",
    "What Happens During a Retail Store IT Refresh",
    "How to Prepare a Store for a POS Hardware Swap Without Closing",
    "Receipt Printer and Payment Terminal Troubleshooting for Store Managers",
    "Grocery and Convenience Store IT: Scanners, Scales and Network Basics",

    # Physical security and building systems
    "How to Choose Security Camera Placement for a Small Business",
    "IP Camera Storage Planning: NVR Sizing and Retention Basics",
    "Door Access Control Upgrades: Keycards, Mobile Credentials and Wiring",
    "Low-Voltage Permits in Arizona: What Business Owners Should Know",
    "Video Intercom Systems for Commercial Buildings: Installation Guide",

    # Office moves and lifecycle
    "Office Move IT Checklist: Disconnecting, Moving and Reconnecting Equipment",
    "How to Decommission Old IT Equipment and Wipe Data Safely",
    "IT Asset Inventory for Small Business: What to Track and Why",
    "Conference Room Technology Setup: Displays, Cameras and Cabling",
    "How to Plan Printer and Copier Networking in a Shared Office",

    # Field service operations
    "What a Good IT Field Service Ticket Includes (and What Delays a Visit)",
    "How Field Technicians Prepare for a Site Visit They've Never Seen",
    "Site Survey Photos: What to Capture Before Any IT Installation",
    "After-Hours IT Work: Planning Installs That Don't Disrupt Business",
    "How MSPs Use Local Field Technicians to Cover Out-of-Area Clients",
    "Preventive Maintenance Visits for Business IT: What Gets Checked",
    "Heat and IT Equipment: Protecting Network Closets in Arizona Summers",
]

_ON_TOPIC = re.compile(
    r"\b(?:it|msp|network(?:s|ing)?|cabl(?:e|es|ing)|fiber|low[- ]voltage|voip|pbx|phone systems?|"
    r"wi-?fi|wireless|switch(?:es)?|firewall|router|poe|rack|idf|mdf|pos|kiosks?|"
    r"technicians?|field service|smart hands|on-site|dispatch|help ?desk|ticket(?:ing)?|"
    r"security cameras?|cameras?|nvr|access control|intercom|digital signage|av installation|"
    r"printers?|data center|server|infrastructure)\b",
    re.I,
)
_STOP = frozenset(
    "a an and at for from how in of on the to with your you guide 2025 2026 2027 free best "
    "what is are vs which why when do does".split()
)


def is_on_topic(text: str) -> bool:
    """True when text is about IT, low-voltage or field-service work."""
    return bool(_ON_TOPIC.search(text or ""))


def _tokens(text: str) -> frozenset[str]:
    stem = re.sub(r"\.md$", "", text.lower())
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    stem = re.sub(r"\bset[- ]up\b", "setup", stem)
    stem = re.sub(r"\bwi[- ]fi\b", "wifi", stem)
    return frozenset(t for t in re.split(r"[^a-z0-9]+", stem) if t and t not in _STOP)


def topic_covered(topic: str, existing_post_names: Iterable[str], threshold: float = 0.6) -> Optional[str]:
    """Return the existing post that already covers topic, if any.

    Generated slugs are shortened forms of the topic title, so this uses the
    overlap coefficient (shared tokens / smaller set) rather than Jaccard.
    """
    wanted = _tokens(topic)
    for name in existing_post_names:
        tokens = _tokens(name)
        if len(tokens) < 3 or not wanted:
            continue
        if len(wanted & tokens) / min(len(wanted), len(tokens)) >= threshold:
            return name
    return None


def pick_topic(existing_post_names: Iterable[str] = (), day_offset: int = 0) -> str:
    """Pick the next uncovered topic, starting from today's day of year."""
    names = list(existing_post_names)
    start = date.today().timetuple().tm_yday + day_offset
    for i in range(len(TOPICS)):
        topic = TOPICS[(start + i) % len(TOPICS)]
        if not topic_covered(topic, names):
            return topic
    raise RuntimeError(
        "Every topic in scripts/article_topics.py is already published; add new "
        "IT/field-service topics before the next run."
    )


if __name__ == "__main__":
    import os
    import sys

    posts_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    existing = os.listdir(posts_dir) if posts_dir else []
    print(pick_topic(existing))
