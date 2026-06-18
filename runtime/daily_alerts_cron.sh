#!/bin/bash
#
# ProfitEngine Daily Alert Cron Job
# Runs every day at 5 PM MST (market close)
#
# To install:
#   crontab -e
# Then add this line:
#   0 23 * * * cd /path/to/runtime && python3 daily_alerts.py >> daily_alerts.log 2>&1
#
# Note: 23:00 UTC = 5 PM MST (during daylight saving time)
#       For standard time, use 00:00 (6 PM MST)
#       Check current UTC offset: date +%Z
#
# Alternative: Use systemd timer instead (see daily_alerts.timer and daily_alerts.service)

# Source environment if needed
if [ -f /etc/profile ]; then
    source /etc/profile
fi

if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Change to runtime directory
cd "$(dirname "$0")" || exit 1

# Run the daily alerts script
/usr/bin/python3 daily_alerts.py

# Log execution
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Daily alerts executed" >> daily_alerts.log
