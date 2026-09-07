# Google Sheets Daily Metrics Tracker — Setup Guide

## Quick Start

1. Create new Google Sheet: "ProfitEngine Daily Metrics"
2. Copy headers from "Sheet Template" below
3. Add formulas from "Formula Reference" section
4. Enable notifications for daily updates
5. Share with team in Slack via link

---

## Sheet Template — Header Row

Copy and paste this into your Google Sheet row 1:

```
A1: Date
B1: Day
C1: Email_Sends
D1: Email_Opens
E1: Email_Opens_Pct
F1: Email_Clicks
G1: Email_CTR_Pct
H1: Email_CTOR_Pct
I1: Email_Conversions
J1: Email_Conv_Rate_Pct
K1: Email_Revenue_USD
L1: Video_Views_Total
M1: Video_Views_YouTube
N1: Video_Views_TikTok
O1: Video_Views_Instagram
P1: Video_Engagement_Pct
Q1: Video_Watch_Time_Sec
R1: Video_Revenue_USD
S1: Signal_Sent
T1: Signal_Clicks
U1: Signal_CTR_Pct
V1: Signal_Profitable
W1: Signal_Win_Rate_Pct
X1: Signal_False_Rate_Pct
Y1: Signal_Revenue_USD
Z1: Twitter_Impressions
AA1: Twitter_Engagement_Pct
AB1: Twitter_Clicks
AC1: Instagram_Reach
AD1: Instagram_Engagement_Pct
AE1: Instagram_Clicks
AF1: TikTok_Reach
AG1: TikTok_Engagement_Pct
AH1: TikTok_Clicks
AI1: Total_Daily_Revenue_USD
AJ1: Running_Weekly_Total_USD
AK1: Notes
```

---

## Formula Reference

### Email Metrics Formulas

**Email Open Rate % (Column E)**
```
=IF(C2=0,0,(D2/C2)*100)
```
Calculates: Opens ÷ Sends × 100

**Email CTR % (Column G)**
```
=IF(D2=0,0,(F2/D2)*100)
```
Calculates: Clicks ÷ Opens × 100

**Email CTOR % (Column H)**
```
=IF(D2=0,0,(F2/D2)*100)
```
Calculates: Unique Clicks ÷ Opens × 100

**Email Conversion Rate % (Column J)**
```
=IF(F2=0,0,(I2/F2)*100)
```
Calculates: Conversions ÷ Clicks × 100

**Email Revenue $ (Column K)**
```
=F2*J2/100*45
```
Calculates: Clicks × Conversion Rate × $45 avg commission per transaction

---

### Video Metrics Formulas

**Total Video Views (Column L)**
```
=M2+N2+O2
```
Calculates: YouTube + TikTok + Instagram views

**Video Engagement % (Column P)**
```
=IF(L2=0,0,(Q2/L2)*100)
```
Engagement rate based on watch time vs total views

**Video Revenue $ (Column R)**
```
=L2*0.02*0.01*50
```
Calculates: Views × 2% click rate × 1% conversion × $50 commission

**Alternative Video Revenue (higher accuracy)**
```
=SUMIF(L:L,L2,(L:L*0.02*0.01*50))
```

---

### Trading Signal Metrics Formulas

**Signal CTR % (Column U)**
```
=IF(S2=0,0,(T2/S2)*100)
```
Calculates: Clicks ÷ Signals Sent × 100

**Signal Win Rate % (Column W)**
```
=IF(V2=0,0,(V2/S2)*100)
```
Calculates: Profitable Trades ÷ Total Signals × 100

**Signal False Rate % (Column X)**
```
=(S2-V2)/S2*100
```
Calculates: (Total - Profitable) ÷ Total × 100

**Signal Revenue $ (Column Y)**
```
=V2*200
```
Calculates: Profitable Trades × $200 avg profit per winning signal

---

### Social Media Metrics Formulas

**Twitter Engagement % (Column AA)**
```
=IF(Z2=0,0,(AB2/Z2)*100)
```
Calculates: Clicks ÷ Impressions × 100

**Instagram Engagement % (Column AD)**
```
=IF(AC2=0,0,(AE2/AC2)*100)
```
Calculates: Clicks ÷ Reach × 100

**TikTok Engagement % (Column AG)**
```
=IF(AF2=0,0,(AH2/AF2)*100)
```
Calculates: Clicks ÷ Reach × 100

---

### Daily & Weekly Revenue Formulas

**Total Daily Revenue $ (Column AI)**
```
=K2+R2+Y2
```
Calculates: Email Revenue + Video Revenue + Signal Revenue

**Running Weekly Total $ (Column AJ)**
```
=SUM($K$2:K2)+SUM($R$2:R2)+SUM($Y$2:Y2)
```
Calculates: Cumulative revenue from row 2 to current row

**Running Weekly Total (Alternative for Sunday reset)**
```
=IF(B2="Sunday",AI2,AI2+AJ1)
```
Resets each Sunday, cumulates Mon-Sat

---

## Conditional Formatting Rules

Apply these to highlight performance:

### Email CTR (Column G) — Highlight if below target
- Format cells if: `Custom formula is: =G2<2.5`
- Fill color: Light Red (underperforming)
- Condition 2: `Custom formula is: =G2>4`
- Fill color: Light Green (high performer)

### Video Engagement (Column P)
- Format cells if: `Custom formula is: =P2<3`
- Fill color: Light Red
- Condition 2: `Custom formula is: =P2>5`
- Fill color: Light Green

### Signal Win Rate (Column W)
- Format cells if: `Custom formula is: =W2<50`
- Fill color: Light Red
- Condition 2: `Custom formula is: =W2>60`
- Fill color: Light Green

### Daily Revenue (Column AI)
- Format cells if: `Custom formula is: =AI2<150`
- Fill color: Light Red
- Condition 2: `Custom formula is: =AI2>250`
- Fill color: Light Green

---

## Charts to Create

### 1. Daily Revenue Trend (Line Chart)
- X-axis: Date (Column A)
- Y-axis: Total Daily Revenue (Column AI)
- Adds: Shows $150 target line (add benchmark series)
- Refresh: Daily at 6 PM

### 2. Conversion Funnel (Column Chart)
- Shows: Email Sends → Opens → Clicks → Conversions
- Formula series: 
  - Sends: =C2
  - Opens: =D2
  - Clicks: =F2
  - Conversions: =I2
- Enables: Visual drop-off identification

### 3. Channel Performance (Stacked Column)
- Email Revenue: =K2
- Video Revenue: =R2
- Signal Revenue: =Y2
- Enables: Revenue mix analysis

### 4. Weekly Cumulative Revenue (Area Chart)
- Series: Running Weekly Total (Column AJ)
- Target line: $1,000
- Shows: 7-day accumulation progress

---

## Data Entry Guide

### Morning (8 AM) — Fill These Columns
- A: Today's date
- B: Day of week
- C: Total emails sent so far
- S: Trading signals sent
- Z: Twitter impressions
- AC: Instagram reach
- AF: TikTok reach
- AK: Any notes

### Midday (12 PM) — Update
- D: Email opens (from yesterday 11 PM to now)
- F: Email clicks
- L: Video views
- T: Signal clicks

### Afternoon (3 PM) — Update
- D: Running total of opens
- F: Running total of clicks
- L: Running total of video views
- V: Profitable trades count

### Evening (6 PM) — Final Fill
- All remaining columns
- Formulas auto-calculate
- AI: Daily revenue appears
- AJ: Weekly total updates

---

## Automated Notifications (Google Apps Script)

Copy this script into Apps Script editor (Tools > Script Editor):

```javascript
function sendDailyMetricAlert() {
  var sheet = SpreadsheetApp.getActive().getSheetByName("Metrics");
  var lastRow = sheet.getLastRow();
  
  // Get today's metrics
  var date = sheet.getRange("A" + lastRow).getValue();
  var dailyRevenue = sheet.getRange("AI" + lastRow).getValue();
  var emailCTR = sheet.getRange("G" + lastRow).getValue();
  var videoEngagement = sheet.getRange("P" + lastRow).getValue();
  var signalWinRate = sheet.getRange("W" + lastRow).getValue();
  
  // Format message
  var message = "ProfitEngine Daily Metrics - " + date + "\n" +
    "Daily Revenue: $" + dailyRevenue.toFixed(2) + "\n" +
    "Email CTR: " + emailCTR.toFixed(2) + "%\n" +
    "Video Engagement: " + videoEngagement.toFixed(2) + "%\n" +
    "Signal Win Rate: " + signalWinRate.toFixed(2) + "%";
  
  // Send to Slack (requires webhook)
  var payload = {
    text: message
  };
  
  var options = {
    method: "post",
    payload: JSON.stringify(payload)
  };
  
  // Set your Slack webhook URL via Script Properties (never hardcode secrets)
  var webhookUrl = PropertiesService.getScriptProperties().getProperty("SLACK_WEBHOOK_URL");
  UrlFetchApp.fetch(webhookUrl, options);
}

function setupDailyTrigger() {
  ScriptApp.newTrigger("sendDailyMetricAlert")
    .timeBased()
    .atHour(18) // 6 PM
    .everyDays(1)
    .create();
}
```

**To enable:**
1. Open Apps Script (Tools > Script Editor)
2. Paste code above
3. Set your Slack webhook URL
4. Run `setupDailyTrigger()` once
5. Grant permissions when prompted

---

## Slack Integration with Sheets

### Publish Daily Summary Automatically

**Option 1: Google Sheets + Slack App**
1. Install "Slack for Google Sheets" from Add-ons
2. Configure to post to #daily-execution channel
3. Set trigger for 6 PM daily
4. Choose columns to display: A, D, F, AI (Date, Opens, Clicks, Revenue)

**Option 2: Webhook + Apps Script (manual)**
1. Create Slack webhook: `api.slack.com/apps` → Your App → Incoming Webhooks
2. Add webhook URL to Apps Script above
3. Run trigger at 6 PM daily
4. Message appears in #daily-execution automatically

---

## Weekly Summary Tab

Create a second sheet called "Weekly Summary" with this header:

```
A: Week_Starting_Date
B: Email_Opens_Total
C: Email_CTR_Avg_Pct
D: Email_Revenue_Total
E: Video_Views_Total
F: Video_Engagement_Avg_Pct
G: Video_Revenue_Total
H: Signal_Win_Rate_Avg_Pct
I: Signal_Revenue_Total
J: Total_Weekly_Revenue
K: Achievement_vs_Target_Pct
L: Notes
```

**Weekly Revenue Formula (K column)**
```
=J2/1000*100
```
Target is $1,000, so this shows achievement %

---

## Mobile View Setup

Google Sheets automatically responds to mobile, but optimize by:

1. Hide columns: M-AK (detailed metrics)
2. Show only: A, D, F, AI (Date, Opens, Clicks, Revenue)
3. Pin headers (Data > Named ranges, set first row)
4. Add "Last Updated" cell with formula:
   ```
   =TEXT(NOW(),"MM/DD/YYYY HH:MM:SS")
   ```

---

## Backup & Version Control

**Weekly Backup:**
- File > Version history > Every Sunday 6 PM
- Name: "Weekly_Backup_WEEK_OF_[DATE]"
- Keeps previous 30 days of versions

**Export CSV:**
```
File > Download > Comma Separated Values (.csv)
```
Run every Sunday, save to: `/backups/metrics_[DATE].csv`

---

## Troubleshooting

**Formulas show error?**
- Check cell references match your column layout
- Ensure all input columns have data before formula runs
- Use `=IF(ISBLANK(C2),"",FORMULA_HERE)` to handle empty cells

**Charts not updating?**
- Hard refresh (Ctrl+Shift+R on Windows)
- Check data range includes entire column (not just fixed rows)
- Delete and recreate chart if stuck

**Slack notifications not arriving?**
- Verify webhook URL in Apps Script
- Check Slack channel permissions
- Test with `sendDailyMetricAlert()` manual run in Apps Script editor

**Performance issues with 365+ rows?**
- Archive old data to "2024 Q1 Metrics" sheet
- Keep main "Metrics" sheet to last 90 days only
- Use SUMIF formulas to reference archived data

---

## Export & Archive Workflow

**Monthly (Last Sunday of month, 6 PM):**
1. Run export: File > Download > CSV
2. Save as: `ProfitEngine_Metrics_[MONTH]_[YEAR].csv`
3. Upload to: Google Drive > Backups folder
4. Create summary chart in separate "Analysis" sheet
5. Post weekly revenue summary to #weekly-reports Slack

**Quarterly:**
1. Create new "Q[#] [YEAR]" folder in Google Drive
2. Move monthly CSVs into folder
3. Create quarterly analysis PDF
4. Archive old sheets to "Archive" folder in Drive

---

## Direct Copy-Paste Shortcuts

**Paste entire formula set** (for rows 2-365):
```
Copy all formulas from row 2
Select range G2:AJ2
Ctrl+D (Windows) or Cmd+D (Mac)
All formulas fill down for next 363 days
```

**Conditional formatting bulk apply:**
1. Format row 2 completely
2. Select A2:AJ2
3. Format painter > select A3:AJ365
4. All formatting copies down

---

## Links & Templates

- Google Sheets Template: [Create new sheet, copy headers above]
- Slack Webhook Setup: https://api.slack.com/apps
- Apps Script Editor: script.google.com
- Google Drive Backups: drive.google.com
