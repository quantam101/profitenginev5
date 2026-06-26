#!/bin/bash
# Real-time Post Monitor with Direct Links
# Watch OCI logs and display posts with clickable links

echo "════════════════════════════════════════════════════════════════"
echo "  PROFITENGINE v5 - REAL-TIME POST MONITOR"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Watching for posts... (Ctrl+C to stop)"
echo ""

# SSH into OCI and stream logs with real-time filtering
ssh -i ~/.ssh/cmdos_deploy_key ubuntu@129.146.236.177 << 'EOF' &

LOGFILE="/home/ubuntu/video_generation.log"

# Function to extract post links based on platform
get_platform_link() {
  local platform=$1
  case $platform in
    "TikTok")
      echo "https://www.tiktok.com/@alreadyherellc/video/[ID]"
      ;;
    "Twitter")
      echo "https://twitter.com/alreadyherellc/status/[ID]"
      ;;
    "YouTube")
      echo "https://www.youtube.com/c/AlreadyHereLLC"
      ;;
    "LinkedIn")
      echo "https://www.linkedin.com/company/already-here-llc"
      ;;
    "Instagram")
      echo "https://www.instagram.com/alreadyherellc"
      ;;
    "Facebook")
      echo "https://www.facebook.com/alreadyherellc"
      ;;
    "Telegram")
      echo "https://t.me/alreadyherellc"
      ;;
  esac
}

# Watch for post success messages
tail -f "$LOGFILE" 2>/dev/null | grep -E "Posted to|✅" | while read line; do
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  # Extract platform name
  if [[ $line =~ "Posted to "([A-Za-z]+) ]]; then
    platform="${BASH_REMATCH[1]}"

    clear
    echo ""
    echo "🚀 NEW POST DETECTED!"
    echo "════════════════════════════════════════════════════════════════"
    echo "  Timestamp: $timestamp"
    echo "  Platform: $platform"
    echo "  Status: ✅ POSTED SUCCESSFULLY"
    echo ""
    echo "  View Post:"
    echo "  $(get_platform_link "$platform")"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Latest log line: $line"
    echo ""
  fi
done

EOF

wait
