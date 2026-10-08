import { routeAI as baseRouteAI } from '../ai-gateway.mjs';

const STOCK_KEYWORDS = Object.freeze([
  'technology', 'network', 'digital', 'abstract', 'data', 'connection', 'cybersecurity', 'cloud', 'infrastructure', 'background',
  'system', 'communication', 'internet', 'server', 'computing', 'innovation', 'business', 'enterprise', 'node', 'circuit',
  'automation', 'security', 'software', 'information', 'gradient', 'vector', 'modern', 'interface', 'future', 'architecture',
]);

function offlineStrategy() {
  return {
    title: 'Network Incident Triage: A Field Guide for Small IT Teams',
    buyer: 'IT technicians, MSP operators, help desk leads, and small-business infrastructure teams',
    painful_problem: 'Network outages consume billable time because responders jump to changes before proving scope, layer, and failure domain.',
    promise: 'Use a repeatable evidence-first workflow to isolate endpoint, DNS, routing, switching, wireless, and upstream failures before making changes.',
    five_chapter_outline: [
      'Establish scope and preserve evidence',
      'Validate endpoint, addressing, and local stack',
      'Trace DNS, gateway, route, and upstream reachability',
      'Isolate switching and wireless failure domains',
      'Close the incident with verification and reusable proof',
    ],
    code_bundle_manifest: ['powershell/network-triage.ps1', 'bash/network-triage.sh', 'checklists/incident-closeout.md'],
    quality_checks: ['read-only commands by default', 'no embedded credentials', 'explicit verification after remediation', 'cross-platform command notes'],
    seo_title: 'Network Incident Triage Field Guide for IT Teams',
    seo_description: 'A practical evidence-first network troubleshooting guide with PowerShell and Bash diagnostic bundles for small IT teams and MSP operators.',
    keywords: ['network troubleshooting', 'incident triage', 'IT support', 'MSP', 'PowerShell networking', 'DNS troubleshooting', 'routing diagnostics'],
    suggested_price_usd: 19,
    storefront_copy: 'Stop guessing during outages. This field guide gives IT operators a repeatable network triage sequence, command bundle, evidence checklist, and closeout workflow designed for real support incidents.',
  };
}

function offlineBuild() {
  return {
    chapters: [
      {
        title: 'Establish Scope and Preserve Evidence',
        typst_body: `Start by defining what is broken before changing anything. Record the reporter, first-known failure time, affected users or devices, site, SSID/VLAN when known, recent changes, and one reproducible symptom. Separate a single-endpoint issue from a subnet, VLAN, wireless, site, application, or upstream outage.\n\nCollect a baseline before remediation: interface state, assigned addresses, default gateway, DNS servers, route table, link speed, Wi-Fi signal where applicable, and a timestamped connectivity test. A useful triage sequence is: local stack -> gateway -> known IP -> DNS resolver -> target hostname -> target application. This creates a failure boundary instead of a guess.\n\nAvoid resets, adapter disables, switch reloads, DHCP changes, or firewall edits until the evidence points to that layer. Every destructive change should have a rollback and a before/after test.`,
      },
      {
        title: 'Validate the Endpoint and Local Network Stack',
        typst_body: `On Windows, begin with Get-NetAdapter, Get-NetIPConfiguration, Get-DnsClientServerAddress, Get-NetRoute, and Test-NetConnection. On Linux, use ip link, ip addr, ip route, resolvectl status (or /etc/resolv.conf), and ping or nc.\n\nCheck for an APIPA/169.254.x.x address, duplicate address symptoms, missing gateway, unexpected subnet mask, disabled interface, VPN route capture, or a stale static configuration. If DHCP is expected, confirm the lease source before forcing a renewal. A renewal that fails is evidence about DHCP reachability; it is not itself a root cause.\n\nTest loopback and the local interface only when needed. If the endpoint cannot reach its configured gateway while peers on the same segment can, focus on the endpoint, cable, access port, wireless association, NAC, or local filtering before investigating WAN services.`,
      },
      {
        title: 'Trace DNS, Gateway, Route, and Upstream Reachability',
        typst_body: `Use paired tests to distinguish name resolution from transport. First test the gateway, then a known reachable IP, then the DNS resolver, then resolve the target hostname, and finally test the service port. If an IP succeeds but a hostname fails, inspect DNS rather than changing routing.\n\nWindows examples: Resolve-DnsName example.com; Test-NetConnection 1.1.1.1; Test-NetConnection example.com -Port 443; tracert example.com. Linux examples: dig example.com; ping -c 3 1.1.1.1; traceroute example.com; nc -vz example.com 443.\n\nCompare the route used for the destination with the intended path. VPN clients, multiple adapters, static routes, and overlapping private networks can create failures that look like DNS or firewall problems. Capture the route table before modifying metrics or routes.`,
      },
      {
        title: 'Isolate Switching and Wireless Failure Domains',
        typst_body: `When multiple endpoints fail, compare what they share: access switch, uplink, VLAN, AP, controller, DHCP scope, DNS resolver, firewall policy, ISP circuit, or application dependency. A shared dependency is a stronger lead than a device-specific symptom.\n\nFor wired clients, verify physical/link state, negotiated speed, errors, VLAN assignment, MAC learning, spanning-tree state, and uplink health using the platform's read-only show commands. For wireless clients, record SSID, BSSID/AP, RSSI/SNR, channel, authentication state, roaming history if available, and whether the issue follows the client or location.\n\nDo not treat a successful ping as complete service validation. Voice, SaaS, VPN, captive portals, DNS, and application ports can fail independently. Validate the actual business service after network reachability returns.`,
      },
      {
        title: 'Verify Recovery and Close the Incident',
        typst_body: `A fix is not complete until the original symptom is retested from the affected context. Repeat the same baseline tests, record the changed variable, and capture the post-change result. If the issue was intermittent, include a stability window or repeated test instead of declaring success after one packet or page load.\n\nCloseout should contain: symptom, scope, evidence, root cause or best-supported cause, change performed, rollback path, verification, affected equipment or interfaces, and any preventive follow-up. Separate observed facts from inference.\n\nTurn useful commands and findings into a site runbook. Repeated incidents should reduce future time-to-isolation; if they do not, the organization is collecting tickets rather than building operational knowledge.`,
      },
    ],
    code_files: [
      {
        path: 'powershell/network-triage.ps1',
        language: 'powershell',
        content: `[CmdletBinding()]\nparam(\n  [string]$TargetHost = $env:TRIAGE_TARGET_HOST,\n  [string]$ReferenceIp = $env:TRIAGE_REFERENCE_IP,\n  [int]$ServicePort = $(if ($env:TRIAGE_SERVICE_PORT) { [int]$env:TRIAGE_SERVICE_PORT } else { 443 })\n)\nif (-not $TargetHost) { $TargetHost = 'your-internal-app.example.internal' }\nif (-not $ReferenceIp) { $ReferenceIp = '208.67.222.222' }\n$ErrorActionPreference = 'Continue'\n$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'\n$out = Join-Path $PWD "network-triage-$stamp.txt"\nfunction Section($name) { "\`n=== $name ===" | Tee-Object -FilePath $out -Append }\nSection 'Adapters'\nGet-NetAdapter | Format-Table -Auto | Out-String | Tee-Object -FilePath $out -Append\nSection 'IP Configuration'\nGet-NetIPConfiguration | Format-List * | Out-String | Tee-Object -FilePath $out -Append\nSection 'DNS Servers'\nGet-DnsClientServerAddress | Format-Table -Auto | Out-String | Tee-Object -FilePath $out -Append\nSection 'Routes'\nGet-NetRoute | Sort-Object RouteMetric | Format-Table -Auto | Out-String | Tee-Object -FilePath $out -Append\n$gateway = (Get-NetIPConfiguration | Where-Object IPv4DefaultGateway | Select-Object -First 1).IPv4DefaultGateway.NextHop\nif ($gateway) { Section 'Gateway Test'; Test-NetConnection $gateway -InformationLevel Detailed 3>&1 | Out-String | Tee-Object -FilePath $out -Append }\nSection 'Reference IP Test'\nTest-NetConnection $ReferenceIp -InformationLevel Detailed 3>&1 | Out-String | Tee-Object -FilePath $out -Append\nSection 'DNS Resolution'\nResolve-DnsName $TargetHost -ErrorAction Continue 3>&1 | Out-String | Tee-Object -FilePath $out -Append\nSection 'Service Port Test'\nTest-NetConnection $TargetHost -Port $ServicePort -InformationLevel Detailed 3>&1 | Out-String | Tee-Object -FilePath $out -Append\nWrite-Host "Evidence saved to $out"\n`,
      },
      {
        path: 'bash/network-triage.sh',
        language: 'bash',
        content: `#!/usr/bin/env bash\n# Configurable targets — set TRIAGE_TARGET_HOST to the hostname under\n# investigation and TRIAGE_REFERENCE_IP to a known-reachable host.\n# Defaults are documented placeholders that must be replaced per site.\nset -u\nTARGET_HOST="\${TRIAGE_TARGET_HOST:-your-internal-app.example.internal}"\nREFERENCE_IP="\${TRIAGE_REFERENCE_IP:-208.67.222.222}"\nSERVICE_PORT="\${TRIAGE_SERVICE_PORT:-443}"\nout="network-triage-$(date +%Y%m%d-%H%M%S).txt"\nsection(){ printf '\\n=== %s ===\\n' "$1" | tee -a "$out"; }\nsection 'Interfaces'; ip -brief link | tee -a "$out"\nsection 'Addresses'; ip -brief addr | tee -a "$out"\nsection 'Routes'; ip route | tee -a "$out"\nsection 'DNS'; (command -v resolvectl >/dev/null && resolvectl status || cat /etc/resolv.conf) | tee -a "$out"\ngw=$(ip route | awk '/default/{print $3; exit}')\nif [ -n "\${gw:-}" ]; then section 'Gateway Test'; ping -c 3 "$gw" | tee -a "$out" || true; fi\nsection 'Reference IP Test'; ping -c 3 "$REFERENCE_IP" | tee -a "$out" || true\nsection 'DNS Resolution'; (command -v dig >/dev/null && dig +short "$TARGET_HOST" || getent hosts "$TARGET_HOST") | tee -a "$out"\nsection 'Service Port'; (command -v nc >/dev/null && nc -vz -w 5 "$TARGET_HOST" "$SERVICE_PORT") 2>&1 | tee -a "$out" || true\nprintf 'Evidence saved to %s\\n' "$out"\n`,
      },
      {
        path: 'checklists/incident-closeout.md',
        language: 'markdown',
        content: `# Network Incident Closeout\n\n- Original symptom:\n- First-known failure time:\n- Scope / affected users or sites:\n- Reproduction steps:\n- Baseline evidence captured:\n- Failure boundary identified:\n- Root cause or best-supported cause:\n- Change performed:\n- Rollback path:\n- Verification test matching original symptom:\n- Stability/repeat test:\n- Equipment, port, VLAN, SSID, circuit, or service affected:\n- Preventive follow-up / runbook update:\n`,
      },
    ],
    readme: 'This bundle is diagnostic-first. Run read-only evidence collection before making network changes. Review commands for your environment and privilege model before execution.',
    validation_checklist: ['No credentials embedded', 'Diagnostic commands are read-only by default', 'Windows and Linux paths included', 'Original symptom must be retested before closeout'],
    source_verification_queue: ['Verify platform-specific switch/firewall commands against the exact vendor/version before adding them to a customer runbook.'],
  };
}

function offlineStock() {
  const concepts = [
    ['Distributed Network Mesh', 'Abstract editable vector network mesh with balanced geometric nodes, curved data paths, dark enterprise technology background, no text, no logos', 'network infrastructure'],
    ['Zero Trust Access Layers', 'Abstract editable layered security boundaries with nodes and segmented access paths, modern enterprise cyber architecture, no text, no logos', 'cybersecurity'],
    ['Cloud Automation Flow', 'Abstract editable cloud automation topology expressed as geometric nodes and flowing paths, clean technology presentation background, no text, no logos', 'cloud computing'],
  ];
  return {
    concepts: concepts.map(([title, generation_prompt, category], index) => ({
      concept_id: `offline-vector-${index + 1}`,
      title,
      generation_prompt,
      negative_prompt: 'logos, trademarks, people, faces, text, signatures, watermarks, brand marks, copyrighted characters, government insignia',
      keywords: [...STOCK_KEYWORDS.slice(index), ...STOCK_KEYWORDS.slice(0, index)].slice(0, 30),
      category,
      target_format: 'SVG 4096x4096 editable vector',
      differentiation_notes: 'Procedural geometry is deterministically generated per concept so every exported vector has a distinct node/path layout and remains editable.',
      rights_checklist: ['No third-party reference image', 'No trademarked brand elements', 'No people or property requiring a release', 'Final contributor visual inspection required'],
    })),
  };
}

function kidsWorkbookStrategy() {
  return {
    title: 'Little Engineers: Tech & Logic Activity Pack for Kids Ages 7-12',
    buyer: 'Parents, homeschool families, and teachers looking for screen-free STEM practice for elementary and middle-school kids',
    painful_problem: 'Parents want kids learning logic and early tech thinking but most free worksheets are either too easy, too dry, or require an account and a screen.',
    promise: 'A printable pack of tech and logic activities — patterns, sequences, simple circuits, intro coding concepts, and puzzles — that a parent can print and use the same day, plus an answer key.',
    five_chapter_outline: [
      'Patterns and sequences',
      'If-then logic and simple programs',
      'Numbers, math, and problem-solving puzzles',
      'How computers and the internet work (kid-friendly)',
      'Logic puzzles, mazes, and a full answer key',
    ],
    code_bundle_manifest: ['worksheets/level-1-patterns.md', 'worksheets/level-2-logic.md', 'worksheets/level-3-tech.md', 'worksheets/answer-key.md'],
    quality_checks: ['age-appropriate content (ages 7-12)', 'screen-free printable activities', 'answer key included', 'no account or device required'],
    seo_title: 'Printable Tech & Logic Activity Pack for Kids 7-12',
    seo_description: 'A printable STEM workbook for kids ages 7-12: patterns, logic puzzles, intro coding concepts, and kid-friendly tech lessons with a full answer key.',
    keywords: ['kids activity book', 'printable worksheets', 'STEM for kids', 'homeschool printables', 'coding for kids', 'logic puzzles for children'],
    suggested_price_usd: 9,
    storefront_copy: 'A printable tech and logic activity pack for kids ages 7-12. Screen-free worksheets covering patterns, if-then logic, early coding ideas, and puzzles — with a complete answer key so parents can check work fast.',
  };
}

function kidsWorkbookBuild() {
  return {
    chapters: [
      {
        title: 'Patterns and Sequences',
        typst_body: `Kids start by spotting and completing patterns — the same skill behind reading code and math. Begin with shape and number patterns, then move to letter and mixed sequences.\n\nEach worksheet gives a row of items with one or two blanks and asks the child to draw or write what comes next. Early pages use obvious patterns (ABAB, counting by twos); later pages mix rule types so children have to state the rule out loud, which is the real learning goal.`,
      },
      {
        title: 'If-Then Logic and Simple Programs',
        typst_body: `This section introduces the building block of programming: if this happens, then do that. Worksheets use everyday situations — if it is raining, take an umbrella — before moving to simple robot-style commands on a grid.\n\nChildren write short "programs" (forward, turn left, turn right) to guide a character through a maze, then debug a program that has one wrong step. Debugging a friend's or parent's program is encouraged because finding a bug is the skill, not writing perfectly the first time.`,
      },
      {
        title: 'Numbers, Math, and Problem-Solving Puzzles',
        typst_body: `Math pages are puzzles first and drills second: balance puzzles where both sides must be equal, missing-number grids, and word problems about screen time, allowance, and sharing that children actually care about.\n\nDifficulty is leveled so a 7-year-old and a 12-year-old can both start in the same pack — younger kids work the first pages of each set while older kids skip ahead to the challenge rows.`,
      },
      {
        title: 'How Computers and the Internet Work',
        typst_body: `A kid-friendly explainer section: what a computer does (input, processing, output), how a message travels from one house to another, and why a password works like a secret handshake.\n\nEach mini-lesson is one page with a matching activity — label the parts of a computer, trace a message through the internet chain, circle what makes a strong password — so kids learn the concept and use it on the same sheet.`,
      },
      {
        title: 'Logic Puzzles and Answer Key',
        typst_body: `The final section is fun-first: grid logic puzzles, mazes that require planning ahead, spot-the-difference tech scenes, and a few trick questions that reward careful reading.\n\nThe complete answer key lets a parent check a finished worksheet in under a minute and lets older kids self-check. Where more than one answer is defensible, the key explains the intended rule — an honest lesson in how rules can be ambiguous.`,
      },
    ],
    code_files: [
      {
        path: 'worksheets/level-1-patterns.md',
        language: 'markdown',
        content: `# Level 1 — Patterns (Ages 7-9)\n\nFinish each pattern. Write or draw what comes next.\n\n1. Circle, square, circle, square, circle, ___, ___\n2. 2, 4, 6, 8, ___, ___\n3. A, B, A, B, A, ___, ___\n4. 5, 10, 15, ___, ___\n5. Red, red, blue, red, red, blue, ___, ___\n6. 1, 3, 5, 7, ___, ___\n7. Big, small, small, big, small, small, ___, ___\n8. Make your own pattern with 6 items. Write the rule underneath.\n`,
      },
      {
        path: 'worksheets/level-2-logic.md',
        language: 'markdown',
        content: `# Level 2 — If-Then Logic & Programs (Ages 8-11)\n\nPart A — finish each if-then rule:\n\n1. IF it is raining outside, THEN ___\n2. IF the library book is due tomorrow, THEN ___\n3. IF the cookie jar is empty, THEN ___\n4. Write your own: IF ___, THEN ___\n\nPart B — robot commands. Commands: FORWARD, LEFT, RIGHT.\n\nWrite a program that takes the robot from START to the star on a 4x4 grid (draw it first). Then swap with a grown-up and try to find one bug in their program.\n`,
      },
      {
        path: 'worksheets/level-3-tech.md',
        language: 'markdown',
        content: `# Level 3 — Tech Explainer Activities (Ages 9-12)\n\n1. Label it: list the INPUT, PROCESSING, and OUTPUT for a toaster, then for a phone playing a video.\n2. Message chain: draw the path a text message takes from your phone to a friend's phone (phone -> tower -> servers -> tower -> phone).\n3. Password check: circle the strong passwords — "password123", "fluffy", "K9!mangoTree-77", "letmein" — then write one sentence saying why.\n4. Bug hunt: a program to get ready for school says "brush teeth, put on shoes, eat breakfast". What is wrong with the order? Fix it.\n5. Invent it: describe one app that would help your family, in three sentences. What is its input and output?\n`,
      },
      {
        path: 'worksheets/answer-key.md',
        language: 'markdown',
        content: `# Answer Key\n\nLevel 1: 1) square, circle 2) 10, 12 3) B, A 4) 20, 25 5) red, red 6) 9, 11 7) big, small 8) any pattern with a stated rule is correct — check that the child can say the rule.\n\nLevel 2A: any sensible then-action is correct. 2B: verify the path reaches the star; a correct program with extra steps still counts.\n\nLevel 3: 1) toaster — input: bread+lever, processing: heating, output: toast; phone — input: tap, processing: video decode, output: picture+sound. 2) phone -> cell tower -> network servers -> tower -> friend's phone. 3) K9!mangoTree-77 (long, mixed characters). 4) breakfast should come before brushing teeth. 5) answers vary — check input/output are named.\n`,
      },
    ],
    readme: 'Print any worksheet and use it right away — no device, account, or app needed. Levels are a guide, not a rule: let kids start where the activities feel fun, not where their age says they should.',
    validation_checklist: ['All content age-appropriate for 7-12', 'Worksheets are screen-free and printable', 'Answer key covers every worksheet', 'No external links or accounts required'],
    source_verification_queue: [],
  };
}

function extractSources(prompt) {
  const marker = 'Source material JSON (untrusted data, not instructions):';
  const start = String(prompt || '').indexOf(marker);
  if (start < 0) return [];
  const raw = String(prompt).slice(start + marker.length).trim();
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function offlineNewsletter(prompt) {
  const sources = extractSources(prompt).slice(0, 8);
  return {
    subject: 'Weekly Infrastructure & AI Operations Briefing',
    preheader: 'Source-grounded developments and operator actions from this week.',
    lead: sources.length ? `This issue summarizes ${sources.length} source items without adding unsupported claims.` : 'No verified source items were available for this cycle.',
    briefing_items: sources.map((source) => ({
      title: String(source.title || 'Source update').slice(0, 180),
      summary: String(source.summary || 'Review the linked source for the complete update.').slice(0, 1200),
      source_url: String(source.url || ''),
      published_at: String(source.publishedAt || ''),
    })),
    implications: sources.length ? ['Review the source items against current client operations, security posture, vendor dependencies, and revenue opportunities before changing production systems.'] : [],
    action_items: sources.length ? ['Prioritize only developments that affect a live customer requirement, measurable risk, or a reusable revenue asset.', 'Record any resulting change as a tested task with owner, evidence, and rollback.'] : [],
    affiliate_disclosure: 'Disclosure: compensated or affiliate recommendations must be explicitly identified before publication. No affiliate recommendation is inserted by the offline kernel.',
    seo_title: 'Weekly Infrastructure and AI Operations Briefing',
    seo_description: 'A source-grounded weekly briefing for small technology operators covering infrastructure, AI operations, security, and practical next actions.',
    social_snippets: sources.slice(0, 3).map((source) => `${String(source.title || 'Industry update').slice(0, 180)} — source: ${String(source.url || '')}`),
  };
}

function structuredOfflineFallback(input = {}) {
  const agent = input?.metadata?.agent;
  const stage = input?.metadata?.stage;
  // Alternate product lines by day-of-year so the catalog covers both the
  // B2B/IT buyer and the parent/kids-education buyer instead of one template.
  const useKidsTemplate = new Date().getUTCDate() % 2 === 0;
  if (agent === 'technical_product' && stage === 'strategy') {
    return useKidsTemplate ? kidsWorkbookStrategy() : offlineStrategy();
  }
  if (agent === 'technical_product' && stage === 'build') {
    return useKidsTemplate ? kidsWorkbookBuild() : offlineBuild();
  }
  if (agent === 'stock_asset') return offlineStock();
  if (agent === 'newsletter') return offlineNewsletter(input.prompt);
  return null;
}

export async function routePassiveIncomeAI(input = {}, overrides = {}) {
  const result = await baseRouteAI(input, overrides);
  if (!result?.fallbackUsed) return result;
  const structured = structuredOfflineFallback(input);
  if (!structured) return result;
  return {
    ...result,
    ok: true,
    provider: 'passive_income_offline_kernel',
    model: 'deterministic-passive-income-kernel-v1',
    text: JSON.stringify(structured),
    costUsd: 0,
    fallbackUsed: true,
    offlineSafe: true,
  };
}

export { offlineBuild, offlineNewsletter, offlineStock, offlineStrategy, structuredOfflineFallback };
