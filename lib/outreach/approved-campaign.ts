import type { CreateOutreachInput } from './types';

const signature = `\n\nStephen Franklin\nAlready Here LLC\n602-882-2920\ndispatch@alreadyherellc.com`;

export const approvedPhoenixCampaign: CreateOutreachInput[] = [
  {
    company: 'Launch IT Proactive Solutions',
    lane: 'MSP overflow',
    source: 'approved-phoenix-outreach-2026-07-19:launch-it',
    recipients: { to: ['info@launchits.com'] },
    subject: 'Phoenix White-Label Onsite IT and Emergency Field Coverage',
    body: `Hello Launch IT Operations Team,\n\nAlready Here LLC provides white-label onsite execution across Phoenix, Chandler, Tempe, Mesa, Scottsdale and the East Valley. Services include router, firewall, switch and access-point support; server-room smart hands; endpoint and printer troubleshooting; hardware replacement; office moves; site surveys; remote-engineer coordination; and documented evening, weekend and emergency closeout.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, urgency, access, travel and documentation. Fixed-project and reserved-capacity arrangements are available. Please send any current onsite ticket, project scope, service area and approved budget for review.${signature}`,
  },
  {
    company: 'Bolt Forward',
    lane: 'MSP overflow',
    source: 'approved-phoenix-outreach-2026-07-19:bolt-forward',
    recipients: { to: ['info@boltforward.com'] },
    subject: 'Phoenix MSP Overflow and Onsite Technical Support',
    body: `Hello Bolt Forward Operations Team,\n\nAlready Here LLC provides Phoenix-area white-label field support for managed-service providers, including Cisco switching, routing and wireless support; VMware and server smart hands; endpoint troubleshooting; hardware replacement; office refreshes; printer support; remote-engineer coordination; asset documentation; and after-hours response.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, urgency, travel, site access and closeout requirements. Fixed-project, recurring and reserved-capacity pricing is available. Please send any current backlog or upcoming Phoenix-area requirement for review.${signature}`,
  },
  {
    company: 'AVCOMM Technology Solutions',
    lane: 'Low voltage and AV',
    source: 'approved-phoenix-outreach-2026-07-19:avcomm',
    recipients: { to: ['info@avcommtech.com'] },
    subject: 'Phoenix Low-Voltage, Cabling and AV Project Overflow',
    body: `Hello AVCOMM Operations Team,\n\nAlready Here LLC provides Phoenix-area field execution for structured cabling, low-voltage, AV, network and security projects. We support cable installation and remediation, access-point and camera installation, rack and patch-panel work, AV mounting, site surveys, punch-list completion, remote project-manager coordination and short-notice coverage in healthcare, retail, education and commercial environments.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, urgency, access, travel and closeout requirements. Fixed-project and recurring-capacity pricing is available. Please send any project backlog, punch-list or scheduled rollout requiring additional field capacity.${signature}`,
  },
  {
    company: 'Phoenix Computer Recycle',
    lane: 'ITAD and decommissioning',
    source: 'approved-phoenix-outreach-2026-07-19:phoenix-computer-recycle',
    recipients: { to: ['info@phoenixcomputerrecycle.com'], cc: ['recycle@techbrosaz.com'] },
    subject: 'Phoenix ITAD and Data-Center Decommissioning Support',
    body: `Hello Phoenix Computer Recycle Operations Team,\n\nAlready Here LLC provides Phoenix-area field execution for IT asset disposition, equipment recovery and data-center decommissioning, including server and network deinstallation, rack and cable removal, serial and MAC capture, inventory reconciliation, condition photography, packing, palletization, loading, cargo-van and utility-trailer logistics, and documented chain of custody.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, urgency, access, travel and documentation. Fixed-project, per-site and recurring-capacity pricing is available. Please send any current pickup, teardown, closure or data-center scope for review.${signature}`,
  },
  {
    company: 'EWaste Phoenix',
    lane: 'ITAD and decommissioning',
    source: 'approved-phoenix-outreach-2026-07-19:ewaste-phoenix',
    recipients: { to: ['info@ewastephoenix.com'], cc: ['itad@techbrosaz.com'] },
    subject: 'Phoenix Weekend ITAD and Asset-Recovery Overflow',
    body: `Hello EWaste Phoenix Operations Team,\n\nAlready Here LLC is available for Phoenix-area ITAD and data-center overflow, including server and network deinstallation, rack and cable removal, serialized inventory, condition photography, chain-of-custody documentation, packing, palletization, cargo-van and utility-trailer transportation, and evening or weekend project support.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, priority, access, travel and closeout requirements. Fixed-project and reserved weekend-capacity pricing is available. Please send any current pickup backlog, teardown requirement or upcoming Phoenix project.${signature}`,
  },
  {
    company: 'MedTech AZ',
    lane: 'Biomedical field service and logistics',
    source: 'approved-phoenix-outreach-2026-07-19:medtech-az',
    recipients: { to: ['service@medtechaz.com'] },
    subject: 'Phoenix Biomedical Field-Service and Equipment Logistics Support',
    body: `Hello MedTech AZ Service Team,\n\nMy biomedical background includes GE Healthcare field service involving installation, preventive maintenance, calibration, electrical-safety testing, performance verification, component replacement, incoming inspection and restoration of clinical capability. Already Here LLC can support service overflow, PM routes, equipment pickup and return, installation assistance, functional checks, serial capture, clinic and hospital support, and end-of-life equipment logistics.\n\nCommercial dispatches are priced at $95-$195 per hour depending on scope, urgency, access, travel and documentation. Fixed-route, project and reserved-capacity pricing is available. Please send any current Phoenix service backlog, equipment list or route requirement.${signature}`,
  },
  {
    company: 'Cloud Destinations',
    lane: 'Network security contract',
    source: 'approved-phoenix-outreach-2026-07-19:cloud-destinations',
    recipients: { to: ['careers@clouddestinations.com'], cc: ['kavyaga@clouddestinations.com'] },
    subject: 'Network Security Deployment Engineer - Stephen Franklin',
    body: `Hello Cloud Destinations Recruiting Team,\n\nI am applying for the Network Security Deployment Engineer contract. My experience includes Cisco enterprise switching and routing, Layer 2/3 troubleshooting, 802.1X, RADIUS and AAA, network access control and segmentation, Zero Trust infrastructure, change planning and rollback, Python automation, multi-site deployments and post-change validation.\n\nPlease confirm C2C availability through Already Here LLC, expected weekly hours, onsite travel frequency, paid travel time and expenses, maintenance-window expectations and the interview timeline. I am targeting $80 per hour C2C, with all required travel separately covered.${signature}`,
  },
];
