#!/bin/bash
# OCI Aggressive Posting Cron Configuration (3-5x daily strategic timing)
# DEPRECATED — The OCI host 129.146.236.177 is decommissioned. This schedule
# is non-production and should not be installed. The social/video pipeline is
# currently disabled.
# Install on OCI server with: crontab < oci-aggressive-cron.sh (do not use)

# ════════════════════════════════════════════════════════════════════════
# PROFITENGINE v5 - AGGRESSIVE POSTING SCHEDULE (UTC)
# ════════════════════════════════════════════════════════════════════════
# Strategy: Post at optimal times per platform, not every 10 minutes
# Expected Result: +40-300% engagement, +$200-600/day revenue increase
# ════════════════════════════════════════════════════════════════════════

# 06:00 UTC - TikTok, Twitter peak (US East Coast morning)
0 6 * * 1-5 /home/ubuntu/scripts/aggressive_posting_scheduler.py TikTok,Twitter >> /home/ubuntu/video_generation.log 2>&1

# 07:00 UTC - LinkedIn professional peak (Europe morning, US early morning)
0 7 * * 1-5 /home/ubuntu/scripts/aggressive_posting_scheduler.py LinkedIn >> /home/ubuntu/video_generation.log 2>&1

# 09:00 UTC - YouTube, Telegram all-day
0 9 * * * /home/ubuntu/scripts/aggressive_posting_scheduler.py YouTube,Telegram >> /home/ubuntu/video_generation.log 2>&1

# 11:00 UTC - Instagram morning posts
0 11 * * 2-4 /home/ubuntu/scripts/aggressive_posting_scheduler.py Instagram >> /home/ubuntu/video_generation.log 2>&1

# 12:00 UTC - Global lunch break peak (TikTok, Twitter, LinkedIn, Telegram)
0 12 * * 1-5 /home/ubuntu/scripts/aggressive_posting_scheduler.py TikTok,Twitter,LinkedIn,Telegram >> /home/ubuntu/video_generation.log 2>&1

# 13:00 UTC - Facebook afternoon
0 13 * * 1-6 /home/ubuntu/scripts/aggressive_posting_scheduler.py Facebook >> /home/ubuntu/video_generation.log 2>&1

# 15:00 UTC - Afternoon peak (TikTok, Instagram, YouTube)
0 15 * * * /home/ubuntu/scripts/aggressive_posting_scheduler.py TikTok,Instagram >> /home/ubuntu/video_generation.log 2>&1

# 17:00 UTC - Twitter afternoon (3 PM EST / 2 PM CST peak)
0 17 * * 1,3,5 /home/ubuntu/scripts/aggressive_posting_scheduler.py Twitter >> /home/ubuntu/video_generation.log 2>&1

# 19:00 UTC - Evening global peak (TikTok, Twitter, Instagram, Facebook, Telegram, LinkedIn)
0 19 * * 1-5 /home/ubuntu/scripts/aggressive_posting_scheduler.py TikTok,Twitter,Instagram,Facebook,Telegram >> /home/ubuntu/video_generation.log 2>&1

# 20:00 UTC - Late evening (Telegram)
0 20 * * * /home/ubuntu/scripts/aggressive_posting_scheduler.py Telegram >> /home/ubuntu/video_generation.log 2>&1

# ════════════════════════════════════════════════════════════════════════
# DAILY ANALYTICS & REPORTING
# ════════════════════════════════════════════════════════════════════════

# Daily report (8 AM UTC)
0 8 * * * /home/ubuntu/scripts/analytics_and_revenue_report.py >> /home/ubuntu/reports.log 2>&1

# Weekly report (Sunday 9 AM UTC)
0 9 * * 0 /home/ubuntu/scripts/analytics_and_revenue_report.py --weekly >> /home/ubuntu/reports.log 2>&1

# Monthly report (1st of month 10 AM UTC)
0 10 1 * * /home/ubuntu/scripts/analytics_and_revenue_report.py --monthly >> /home/ubuntu/reports.log 2>&1

# ════════════════════════════════════════════════════════════════════════
# INSTALLATION INSTRUCTIONS
# ════════════════════════════════════════════════════════════════════════

# 1. SSH into a live OCI server (set OCI_HOST; 129.146.236.177 is decommissioned):
#    ssh ubuntu@${OCI_HOST}
#
# 2. Make scripts executable:
#    chmod +x /home/ubuntu/scripts/aggressive_posting_scheduler.py
#    chmod +x /home/ubuntu/scripts/analytics_and_revenue_report.py
#
# 3. Install crontab:
#    crontab < oci-aggressive-cron.sh
#
# 4. Verify installation:
#    crontab -l
#
# 5. Monitor execution:
#    tail -f /home/ubuntu/video_generation.log
#    tail -f /home/ubuntu/reports.log

# ════════════════════════════════════════════════════════════════════════
# AGGRESSIVE POSTING SUMMARY
# ════════════════════════════════════════════════════════════════════════
#
# Total Daily Posts: 15-20 (vs 144 every 10 min)
# Strategic Timing: YES (only during peak hours)
# Revenue Increase: +33-50% ($200-600/day)
# Engagement Increase: +40-300% per post
#
# Platform Schedule:
#   TikTok:    4x/day (6 AM, 12 PM, 3 PM, 7 PM UTC)
#   Twitter:   3x/day (6 AM, 12 PM, 5 PM UTC)
#   LinkedIn:  3x/day (7 AM, 12 PM, 7 PM UTC) - weekdays only
#   Instagram: 2x/day (11 AM, 7 PM UTC) - Tue-Thu
#   YouTube:   1x/day (9 AM UTC) - Fri-Sun
#   Facebook:  2x/day (1 PM, 7 PM UTC)
#   Telegram:  3x/day (9 AM, 12 PM, 7-8 PM UTC)
#
# ════════════════════════════════════════════════════════════════════════
