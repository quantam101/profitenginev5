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
    title: 'Little Engineers: Technology & Logic Workbook - Grades 3-8',
    buyer: 'Classroom teachers, homeschool families, after-school and library programs, and tutors needing a screen-free CS supplement for ages 7-14',
    painful_problem: 'Educators want structured computer-science foundations for elementary and middle grades, but most free worksheets lack standards alignment, differentiation, assessment tools, and answer rationale - so they cannot be used for grading or program adoption.',
    promise: 'A complete print-and-use workbook: six CSTA-aligned units with objectives, vocabulary, mini-lessons, three activity tiers, exit tickets, unplugged games, a facilitator pacing guide, a 4-point rubric, and a full answer key with rationale - covering grades 3-8 in a single product.',
    five_chapter_outline: [
      'Facilitator guide: pacing, differentiation, CSTA alignment, assessment rubric',
      'Units 1-3: patterns, algorithms & debugging, problem-solving puzzles',
      'Units 4-5: how computers & networks work, data & online safety',
      'Unit 6 (teen extension): variables, loops, pseudocode tracing',
      'Assessment rubric, answer key with rationale, glossary, certificate',
    ],
    product_kind: 'workbook',
    code_bundle_manifest: ['workbook/facilitator-guide.md', 'workbook/answer-key.md', 'workbook/certificate.md'],
    quality_checks: ['CSTA 1B/2 standard codes listed per unit', 'three-tier differentiation (Core/Practice/Challenge) in every unit', 'exit ticket + unplugged game per unit', 'answer key includes rationale and acceptable alternatives', 'facilitator pacing and 4-point rubric included', 'screen-free, printable, no accounts required'],
    seo_title: 'Technology & Logic Workbook for Grades 3-8 | Printable STEM Curriculum',
    seo_description: 'A CSTA-aligned printable STEM workbook for ages 7-14: patterns, algorithms, networks, online safety, and pseudocode - with teacher guide, rubric, and answer key for schools and homeschools.',
    keywords: ['STEM workbook', 'computer science elementary', 'homeschool coding curriculum', 'printable worksheets grades 3-8', 'CSTA aligned activities', 'screen-free STEM'],
    suggested_price_usd: 12,
    storefront_copy: 'A complete printable computer-science foundations workbook for grades 3-8 (ages 7-14). Six CSTA-aligned units with mini-lessons, three-tier activities, exit tickets, unplugged classroom games, a facilitator pacing guide, assessment rubric, glossary, answer key with rationale, and a completion certificate. Screen-free - print and teach.',
  };
}

function kidsWorkbookBuild() {
  const unit = (num, title, ages, stds, objectives, vocab, lesson, sections, exitTicket, game) => [
    `## Unit ${num} - ${title} (Ages ${ages})`,
    ``,
    `**CSTA alignment:** ${stds}`,
    ``,
    `**You will learn to:**`,
    ...objectives.map((o) => `- ${o}`),
    ``,
    `**Key vocabulary:** ${vocab}`,
    ``,
    `**Mini-lesson.** ${lesson}`,
    ``,
    ...sections.flatMap(([secTitle, secBody, items]) => [
      `### ${secTitle}`,
      ``,
      secBody,
      ``,
      ...items.map((it, i) => `${i + 1}. ${it}`),
      ``,
    ]),
    `### Exit Ticket`,
    `Before moving on, show what you know:`,
    ...exitTicket.map((q, i) => `${i + 1}. ${q}`),
    ``,
    `**Unplugged game.** ${game}`,
  ].join('\n');

  return {
    chapters: [
      {
        title: 'Facilitator Guide - For Teachers, Parents & Program Leads',
        typst_body: `**Learning objectives.** By the end of this workbook, students will be able to: identify, extend, and create patterns and state their rules; write, follow, and debug step-by-step instructions (algorithms); use IF/THEN/ELSE to describe decisions; decompose problems into smaller parts; describe input, processing, and output for everyday devices; trace a message across a network; explain password strength and safe online behavior; and (extension) read and write pseudocode with variables and loops.

**CSTA standards alignment (K-12 CS Standards, 2017):**
- Unit 1 Patterns: 1B-DA-07, 1B-AP-10 - recognize/describe patterns, develop algorithms
- Unit 2 Algorithms: 1B-AP-08, 1B-AP-11, 2-AP-10 - model processes, decompose problems, flowchart algorithms
- Unit 3 Number Puzzles: 1B-DA-06, 1B-AP-09 - organize/analyze data, solve systematically
- Unit 4 Computers & Networks: 1B-CS-02, 1B-NI-04, 2-NI-04 - systems, network communication
- Unit 5 Safety & Data: 1B-IC-18, 1B-NI-05, 2-IC-23 - information safety, computing impacts
- Unit 6 Teen Programs: 2-AP-11, 2-AP-12, 2-AP-19 - variables, control structures, documentation

**Pacing.** One unit per week: Session 1 = mini-lesson + Core, Session 2 = Practice, Session 3 = Challenge + Exit Ticket + unplugged game. Six weeks total - a natural grading period or enrichment block. Units also work standalone as sub plans or early-finisher packs.

**Differentiation.** Ages 7-9 (Grades 3-4): Core + Practice with adult or buddy support; accept spoken rules instead of written. Ages 10-12 (Grades 5-6): all three tiers independently. Ages 12-14 (Grades 7-8): add Unit 6, require Challenge tier, have students create puzzles for peers.

**Assessment.** Use the 4-point rubric (below) on each Exit Ticket. Mastery target: 3+ per unit. The answer key gives intended answers AND acceptable alternatives - in logic work, a different-but-defensible answer with a stated rule demonstrates mastery.

**Assessment rubric.**
- 4 - Exceeds: states concepts precisely; solves Challenge; creates own example; can teach a peer
- 3 - Meets: correct concept with minor slips; Core + Practice independently; explains reasoning
- 2 - Approaching: partial concept, needs prompts; completes Core with help; partial explanation
- 1 - Beginning: concept not yet grasped; needs step-by-step support on Core`,
      },
      {
        title: 'Unit 1 - Patterns & Sequences (Ages 7-9)',
        typst_body: unit(1, 'Patterns & Sequences', '7-9',
          '1B-DA-07, 1B-AP-10',
          ['Find the rule a pattern follows', 'Extend a pattern forward and backward', 'Build your own pattern and write its rule', 'Explain why computers love patterns'],
          'pattern - something that repeats by a rule; sequence - items in order; rule - the instruction that makes the pattern; algorithm - steps that always work.',
          'A pattern is anything that repeats by a rule. Computers are pattern machines: they spot patterns in photos, music, and numbers faster than any person. The skill is not guessing the next item - it is saying the RULE out loud. \'Add 2\' is a rule. \'Bigger\' is not. Work every problem the same way: (1) look at the first three items, (2) say what changed, (3) say the rule, (4) use the rule to continue.',
          [
            ['Core - Find the rule', 'Continue each pattern for two more items, then write the rule.', ['Circle, square, circle, square, circle, ___, ___', '2, 4, 6, 8, ___, ___  Rule: ______', 'A, B, C, A, B, C, ___, ___  Rule: ______', '5, 10, 15, 20, ___, ___  Rule: ______', 'Z, Y, X, Z, Y, X, ___, ___  Rule: ______', '1, 1, 2, 1, 1, 2, ___, ___  Rule: ______', '100, 90, 80, ___, ___  Rule: ______', 'Draw your own 6-item pattern. Write its rule: ______']],
            ['Practice - Pattern detective', 'One item in each row breaks the rule. Find it and fix it.', ['3, 6, 9, 11, 15 - broken: ___ fix: ___', 'Mon, Tue, Wed, Fri, Thu - broken: ___ fix: ___', '2, 4, 8, 16, 30 - broken: ___ fix: ___', 'A1, B2, C3, D5 - broken: ___ fix: ___', 'A pattern is 4, 8, 12, 16... Is 26 in it? Why or why not?']],
            ['Challenge - Grow it', 'Patterns can grow in two directions and two rules at once.', ['Continue backward AND forward: ___, 7, 14, 21, ___', 'Two rules at once: 1, 2, 4, 8, 16, ___ (each step doubles)', 'Make a shape pattern using BOTH color and size rules.', 'Start with 1, 1 and use the rule \'add the last two numbers\'. What are the next four? (A famous sequence.)', 'Explain why a computer can check 1,000 pattern rows in the time you check one.']],
          ],
          ['State the rule for: 10, 20, 30, 40... ______', 'What makes a good rule? ______', 'One thing you can now do that a computer does too: ______'],
          'Pattern Claps - leader claps a pattern (clap, clap, stomp), group continues it, and must SAY the rule before continuing. Rotate leaders until everyone leads.'),
      },
      {
        title: 'Unit 2 - If-Then Logic & Algorithms (Ages 8-11)',
        typst_body: unit(2, 'If-Then Logic & Algorithms', '8-11',
          '1B-AP-08, 1B-AP-11, 2-AP-10',
          ['Write exact step-by-step instructions', 'Use IF / THEN / ELSE to describe decisions', 'Find and fix the bug in a set of steps', 'Explain why order matters in an algorithm'],
          'algorithm - steps that always finish a task; condition - a true/false question; bug - a mistake in the steps; debug - find and fix a bug.',
          'An algorithm is a recipe for a computer: exact steps, exact order. If any step is missing or out of order, the program fails. Computers decide using conditions: IF something is true THEN do this ELSE do that. Debugging - finding the one wrong step - is the skill employers pay for. A good debugger tests one change at a time.',
          [
            ['Core - If-then rules', 'Finish each rule so a robot could follow it.', ['IF it is raining, THEN ______', 'IF the homework folder is empty, THEN ______', 'IF the battery is below 10%, THEN ______', 'IF (raining) THEN take umbrella, ELSE ______', 'Write a safety rule for crossing a street: IF ______ THEN ______']],
            ['Practice - Be the robot', 'Commands: FORWARD, LEFT, RIGHT. Draw a 5x5 grid, mark S (bottom-left) and star (top-right), then write the program that solves it.', ['Write your program as a numbered list of commands.', 'How many commands did it take? ___', 'Solve it with FEWER commands. Write the shorter program.', 'Deliberately change one command. What happens? (That is a bug.)']],
            ['Challenge - Debug like a pro', 'Each program has exactly one bug. Find it and write the fix.', ['\'Make a sandwich\': 1) put jelly on bread 2) get bread out 3) add peanut butter 4) close. Bug: ___ Fix: ___', '\'Get ready for school\': brush teeth, put on shoes, eat breakfast, leave. Bug: ___ Fix: ___', 'Robot: FORWARD, FORWARD, LEFT, FORWARD - hit a wall at step 3. The fix changes ONE command. What is it?', 'A teammate\'s program works but takes 20 commands; yours takes 8. What makes an algorithm efficient?']],
          ],
          ['An algorithm is ______', 'IF / THEN / ELSE is used when a program needs to ______', 'The bug I found was ______ and I fixed it by ______'],
          'Human Robot - tape a 4x4 grid on the floor. One student is the robot (eyes closed), one reads commands as programmer, one is the debugger watching for errors. Rotate roles; add obstacle squares to raise difficulty.'),
      },
      {
        title: 'Unit 3 - Numbers & Problem-Solving Puzzles (Ages 8-12)',
        typst_body: unit(3, 'Numbers & Problem-Solving Puzzles', '8-12',
          '1B-DA-06, 1B-AP-09',
          ['Solve balance and missing-number puzzles systematically', 'Break a big problem into smaller parts', 'Check an answer by working backward', 'Solve logic grids by eliminating impossible options'],
          'decompose - break a problem into smaller pieces; data - information a computer stores; eliminate - rule out impossible answers.',
          'Programmers decompose problems: instead of \'solve the puzzle\', think \'solve this row first\'. Balance puzzles, missing-number grids, and logic grids all reward the same habit - work one constraint at a time, eliminate the impossible, then check by working backward.',
          [
            ['Core - Balance the scale', 'Both sides must be equal. Fill in the missing number.', ['5 + 3 = ___ + 2', '4 + ___ = 7 + 7', '10 + ___ = 6 + 9', '___ + 8 = 12 + 4', '9 + 9 = ___ + 13', '3 + ___ + 2 = 5 + 6']],
            ['Practice - Word problems programmers write', 'Show the steps, not just the answer.', ['A 90-second video watched 12 seconds a day - how many days to finish?', 'Allowance is $8/week, a game costs $40 - weeks to save? What if you save half plus $2?', '4 classrooms x 6 computers = how many? If 5 are broken, how many work?', 'Screen time: 30 min weekdays, 60 weekend days - minutes and hours per week?']],
            ['Challenge - Logic grid', 'Ada, Bo, Cy each have a different pet (cat, dog, fish) and favorite subject (math, art, science). Clues: (1) Ada does not have the fish. (2) Bo loves science. (3) The dog owner loves math. (4) Cy has the fish. Draw a grid, mark X for impossible and O for certain.', ['Who has the cat? ___', 'Who loves art? ___', 'Explain how clue 4 unlocked the puzzle.']],
          ],
          ['Decompose means ______', 'The strategy that helped me most was ______', 'A problem I can decompose outside this workbook: ______'],
          'Estimation jar - fill a jar with objects; teams estimate, then decompose: count a handful, estimate handfuls per jar, multiply. Closest team explains their method.'),
      },
      {
        title: 'Unit 4 - How Computers & Networks Work (Ages 9-12)',
        typst_body: unit(4, 'How Computers & Networks Work', '9-12',
          '1B-CS-02, 1B-NI-04, 2-NI-04',
          ['Name the input, processing, and output of everyday devices', 'Trace a message across the internet step by step', 'Explain what hardware and software each do', 'Describe what happens when you press send'],
          'input - what goes in; processing - the thinking work; output - what comes out; network - connected devices; server - a computer answering many users; router - traffic director for a home network.',
          'Every device does three things: takes INPUT, does PROCESSING, makes OUTPUT. A toaster: bread + lever in, heating, toast out. Networks pass messages like relay races: phone to router, router to provider, to backbone servers, and back down - in milliseconds.',
          [
            ['Core - Input, processing, output', 'For each device list input, processing, output.', ['Toaster', 'Digital watch', 'Smartphone camera app', 'Elevator button panel', 'School attendance scanner']],
            ['Practice - Trace the message', 'You text \'hi\' to a friend.', ['Put in order: cell tower, your phone, friend\'s phone, network servers.', 'What device sits between your phone and the internet at home? ___', 'A video call freezes. Using phone -> router -> provider -> servers -> phone, name TWO places the problem could be.', 'Which is faster - a message inside your house or between cities? Why?']],
            ['Challenge - Design the system', 'Apply input -> processing -> output as a designer.', ['Design an automatic dog feeder: inputs (buttons, timers, sensors), processing rules, outputs (motor, alert).', 'Your school wants the most popular lunch. Describe the input to collect, the processing, and the output report.', 'A smart doorbell sends video when someone arrives - trace the message path.']],
          ],
          ['IPO for a fridge: ______', 'A server is ______', 'Today I traced a message through ______'],
          'Message relay - whisper a message down a line like packets through routers; compare first vs last. Then add \'error checking\' (repeat back before passing): accuracy up, speed down - a real networking trade-off.'),
      },
      {
        title: 'Unit 5 - Data, Passwords & Staying Safe (Ages 9-12)',
        typst_body: unit(5, 'Data, Passwords & Staying Safe', '9-12',
          '1B-IC-18, 1B-NI-05, 2-IC-23',
          ['Explain what personal data is and why it has value', 'Judge password strength and build strong ones', 'Spot common online tricks (phishing, fake urgency)', 'Decide what is safe to share and what is private'],
          'data - information about you; phishing - fake messages that steal information; private - for you and trusted adults only.',
          'Computers store data - facts about people. Names, birthdays, photos, locations, passwords are worth protecting. A strong password is long and mixes letters, numbers, symbols. Safety rules engineers use: never share passwords, check the sender before clicking, and when something feels rushed or scary - stop and ask an adult.',
          [
            ['Core - Strong or weak?', 'Rate each password STRONG or WEAK and say why.', ['password123', 'fluffy', 'K9!mangoTree-77', 'letmein', 'PurpleTigerDances2!', 'your pet\'s name', 'Write your own strong password PATTERN (not a real one).']],
            ['Practice - Sort the data', 'Label SAFE to share publicly or PRIVATE.', ['Your favorite pizza topping', 'Your home address', 'Your birth date', 'A drawing you made', 'Your school\'s name', 'Your password hints', 'Your phone number', 'Write the rule you used to decide: ______']],
            ['Challenge - Spot the trick', 'Each message has a red flag. Name it.', ['\'URGENT!!! Your account closes in 1 hour - click now!\'  Red flag: ___', '\'Hi, this is your teacher, send me your login.\'  Red flag: ___', '\'You won a prize! Enter your address to claim.\'  Red flag: ___', 'A friend asks for your game password \'just for a minute.\' Write your reply.', 'Why do scammers always add urgency? Explain the trick.']],
          ],
          ['A strong password is ______ and ______', 'The red flag I will watch for is ______', 'Data I keep private: ______'],
          'Password election - groups invent three candidate passwords (never real ones), class votes on the strongest and explains why.'),
      },
      {
        title: 'Unit 6 - Teen Extension: Real Programs (Ages 12-14)',
        typst_body: unit(6, 'Teen Extension: Real Programs', '12-14',
          '2-AP-11, 2-AP-12, 2-AP-19',
          ['Read and write pseudocode with variables', 'Use loops to repeat work without rewriting steps', 'Trace a program line by line and predict output', 'Document what a program does so others can use it'],
          'variable - a named box storing a value; loop - repeat steps; pseudocode - program logic in plain language; trace - follow each line and record changes.',
          'Real programs store values in variables, decide with IF/ELSE, and repeat with loops (FOR, WHILE). Pseudocode example:\n\n    score = 0\n    FOR each question:\n        IF correct THEN score = score + 1\n    DISPLAY score\n\nTracing - following each line and writing what every variable holds - is how professionals find bugs without running anything.',
          [
            ['Core - Trace it', 'Write the final value of each variable.', ['x = 3; x = x + 4; x = x * 2  -> x = ___', 'total = 0; FOR i = 1 to 4: total = total + i  -> total = ___', 'count = 0; FOR letter in \'ROBOT\': count = count + 1  -> count = ___', 'a = 5; b = 2; IF a > b THEN a = a - b ELSE b = b + a  -> a=___, b=___']],
            ['Practice - Write the pseudocode', 'Write pseudocode a teammate could implement without asking questions.', ['Count how many items in a shopping list cost more than $5.', 'Ask for a name and score; say \'You win!\' if score > 100, else \'Try again\'.', 'Locker combination: loop asking for a code until it equals 246 or 3 tries pass.', 'Document program #3 in two sentences a non-programmer understands.']],
            ['Challenge - Find the bug', 'This program should print 1 to 5 but prints 1, 1, 1... forever:\n\n    i = 1\n    WHILE i <= 5:\n        DISPLAY i', ['What is the bug? ___', 'Write the corrected program.', 'Change it to print only EVEN numbers up to 10.', 'Infinite loops are bugs - but name one loop that SHOULD run forever (a device that must never stop).']],
          ],
          ['A variable is ______', 'FOR vs WHILE: ______', 'Today I traced ______ and learned ______'],
          'Living program - students act out a program: one holds a variable card, others read lines aloud, the holder updates the card. The class watches state change in real time.'),
      },
      {
        title: 'Answer Key & Explanations',
        typst_body: `Intended answers with rationale. Acceptable alternatives are listed because in logic work, a different-but-defensible answer with a stated rule demonstrates mastery.

**Unit 1.** Core: 1) square, circle 2) 10, 12 (add 2) 3) A, B (ABC) 4) 25, 30 (add 5) 5) Z, Y (ZYX) 6) 1, 1 (112) 7) 70, 60 (minus 10) 8) any stated rule. Practice: 1) 11 -> 12 2) Fri/Thu swapped 3) 30 -> 32 4) D5 -> D4 5) No - it is multiples of 4 from 4. Challenge: 1) 0 and 28 2) 32 4) 2, 3, 5, 8 (Fibonacci - this famous sequence is a bonus talking point).

**Unit 2.** Core: any sensible action counts; ELSE needs an alternative action. Practice: shortest open-grid program = 8 commands; extra steps are correct but less efficient. Challenge: 1) steps 1-2 swapped 2) breakfast before brushing 3) change LEFT to RIGHT 4) efficient = correct AND short.

**Unit 3.** Core: 6, 10, 5, 8, 5, 6. Practice: 1) 8 days 2) 5 weeks; 7 weeks at half+$2 3) 24 total, 19 working 4) 270 min = 4.5 hr. Challenge: Cy has fish (clue 4), dog owner loves math so it is Ada (Bo loves science), Bo has the cat, Cy loves art. Cat: Bo. Art: Cy.

**Unit 4.** Core: any correct input-processing-output triple (toaster: bread+lever -> heating -> toast). Practice: phone -> tower/router -> servers -> friend's phone; router sits between phone and internet; freeze could be the router or provider link.

**Unit 5.** Core: weak = password123, fluffy, letmein, pet name; strong = K9!mangoTree-77, PurpleTigerDances2! (long + mixed). Practice: SAFE = pizza topping, drawing; PRIVATE = address, birth date, password hints, phone number; school name is debatable - accept reasoned answers. Challenge: fake urgency, impersonation, prize bait; any polite refusal counts; urgency stops thinking - that IS the trick.

**Unit 6.** Core: x=14, total=10, count=5, a=3 b=2. Challenge: i is never incremented (infinite loop); add i = i + 1 inside the loop; evens: start i = 2, step 2; purposeful infinite loops: thermostat monitor, pacemaker.`,
      },
      {
        title: 'Glossary & Certificate',
        typst_body: `**Glossary.** Algorithm - exact steps that always finish a task. Bug - a mistake in a program; debugging fixes it. Condition - a true/false question (IF/THEN/ELSE). Data - information a computer stores. Decompose - break a big problem into smaller pieces. Input/Processing/Output - what goes in, the work, what comes out. Loop - instructions that repeat (FOR, WHILE). Network - connected devices passing messages. Pattern - anything that repeats by a rule. Phishing - fake messages that steal private information. Pseudocode - program logic in plain language. Router - traffic director between home network and internet. Server - a computer answering many users. Variable - a named box storing a value.

**Certificate of Completion.** Award to students who complete all six units (mastery target: 3+ per unit on the rubric).

    This certifies that ______________________________
    has completed all six units of the
    Little Engineers: Technology & Logic Workbook

    Date: ____________   Facilitator: ______________

    Already Here LLC - alreadyherellc.com`,
      },
    ],
    code_files: [
      {
        path: 'workbook/facilitator-guide.md',
        language: 'markdown',
        content: `# Facilitator Guide

Objectives, CSTA alignment table, 6-week pacing plan, differentiation for ages 7-9 / 10-12 / 12-14, and the 4-point assessment rubric are printed in the workbook's opening unit. Suggested use: one unit per week (3 sessions of 30-45 min), or standalone units as sub plans and early-finisher packs.
`,
      },
      {
        path: 'workbook/answer-key.md',
        language: 'markdown',
        content: `# Answer Key (condensed)

Full key with rationale is the workbook's final unit. Unit 1: square-circle / 10,12 / A,B / 25,30 / Z,Y / 1,1 / 70,60. Unit 3 balances: 6,10,5,8,5,6. Unit 3 grid: Bo-cat, Ada-dog+math, Cy-fish+art. Unit 6 traces: x=14, total=10, count=5, a=3 b=2.
`,
      },
      {
        path: 'workbook/certificate.md',
        language: 'markdown',
        content: `# Certificate of Completion

Print and award after all six units are complete (rubric target 3+ per unit).

    This certifies that ______________________________ has completed the
    Little Engineers: Technology & Logic Workbook.
    Date: ____________  Facilitator: ______________
    Already Here LLC - alreadyherellc.com
`,
      },
    ],
    readme: 'Print the workbook single-sided. Six CSTA-aligned units (ages 7-14), facilitator guide with pacing and rubric, exit tickets, unplugged games, answer key with rationale, glossary, and certificate. For classrooms, homeschools, and enrichment programs.',
    validation_checklist: ['CSTA 1B/2 codes present per unit', 'Core/Practice/Challenge tiers in every unit', 'Exit ticket and unplugged game per unit', 'Answer key includes rationale + acceptable alternatives', 'Facilitator guide with pacing + 4-point rubric', 'Screen-free; no accounts, links, or devices required'],
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
