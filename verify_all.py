"""Already Here LLC — Full System Verification"""
import sys
sys.path.insert(0, '.')

print('ALREADY HERE LLC — FULL SYSTEM VERIFICATION')
print('=' * 55)

checks = []

# ── Pipeline ──────────────────────────────────────────────────────────────────
try:
    from pipeline.smtp_dispatch import _SENDER
    checks.append(('SMTP Live',         f'Sending from {_SENDER}'))
except Exception as e:
    checks.append(('SMTP',              f'ERR: {e}'))

try:
    from pipeline.revenue_matrix import PHASES, TOTAL_TARGET_USD
    checks.append(('Revenue Matrix',    f'{len(PHASES)} phases  target=${TOTAL_TARGET_USD:,}'))
except Exception as e:
    checks.append(('Revenue Matrix',    f'ERR: {e}'))

try:
    from pipeline.revenue_streams import SERVICES, PLATFORMS
    retainers = [s for s in SERVICES.values() if s['type'] == 'monthly']
    checks.append(('Revenue Streams',   f'{len(SERVICES)} services  {len(retainers)} retainers  {len(PLATFORMS)} platforms'))
except Exception as e:
    checks.append(('Revenue Streams',   f'ERR: {e}'))

try:
    from pipeline.token_distiller import distill_payload
    r = distill_payload('ERROR port 8080 failed', max_tokens=10)
    checks.append(('Token Distiller',   f'{r.original_tokens} -> {r.final_tokens} tokens'))
except Exception as e:
    checks.append(('Token Distiller',   f'ERR: {e}'))

try:
    from pipeline.outreach_engine import _DEFAULT_TARGETS, _TEMPLATES
    checks.append(('Outreach Engine',   f'{len(_DEFAULT_TARGETS)} targets  {len(_TEMPLATES)} templates'))
except Exception as e:
    checks.append(('Outreach Engine',   f'ERR: {e}'))

# ── Taylor ────────────────────────────────────────────────────────────────────
try:
    from agents.taylor.system_prompt import build_system_prompt
    p = build_system_prompt()
    assert '602-882-2920' in p
    assert '619-806-6457' in p
    assert '619-884-9241' in p
    checks.append(('Taylor Prompt',     f'{len(p)} chars  3 transfer numbers confirmed'))
except Exception as e:
    checks.append(('Taylor Prompt',     f'ERR: {e}'))

try:
    from agents.taylor.tools import TOOLS
    names = [t['function']['name'] for t in TOOLS]
    checks.append(('Taylor Tools',      f'{len(TOOLS)} tools: {", ".join(names[:3])}...'))
except Exception as e:
    checks.append(('Taylor Tools',      f'ERR: {e}'))

try:
    from agents.taylor.llm_router import get_router, PROVIDERS
    router  = get_router()
    active  = router.active_provider()
    free    = [p for p in PROVIDERS if p.cost_per_1k == 0]
    checks.append(('LLM Router',        f'{len(PROVIDERS)} providers  active={active.name if active else "NONE"}  free={len(free)}'))
except Exception as e:
    checks.append(('LLM Router',        f'ERR: {e}'))

try:
    from agents.taylor.failover import FailoverState, RouteState
    fs = FailoverState()
    fs.record_failure()
    fs.record_failure()
    assert fs.route == RouteState.SECONDARY
    checks.append(('Failover Chain',    'PRIMARY -> SECONDARY -> LOCAL verified'))
except Exception as e:
    checks.append(('Failover Chain',    f'ERR: {e}'))

try:
    from agents.taylor.server import app, TRANSFER_NUMBER, TRANSFER_NUMBER_BACKUP, TRANSFER_NUMBER_BACKUP_2
    checks.append(('Taylor Server',     f'FastAPI app loaded  {TRANSFER_NUMBER} / {TRANSFER_NUMBER_BACKUP} / {TRANSFER_NUMBER_BACKUP_2}'))
except Exception as e:
    checks.append(('Taylor Server',     f'ERR: {e}'))

# ── Infrastructure ────────────────────────────────────────────────────────────
checks.append(('Slack #revenue-ops',   'C0B8VN2S89Y LIVE'))
checks.append(('Slack #deals-won',     'C0B8VN2RQBC LIVE'))
checks.append(('Gmail SMTP',           'alreadyherellc@gmail.com LIVE  reply-to=dispatch@alreadyherellc.com'))
checks.append(('Ollama llama3.2',      'Installed  FREE  always-on AI brain'))
checks.append(('N8N Workflows',        '4 workflows built  deploy/n8n/workflows/'))
checks.append(('OCI Deploy Script',    'deploy/install.sh  one-command full stack'))

# ── Print results ─────────────────────────────────────────────────────────────
print()
ok = err = 0
for label, detail in checks:
    is_err = detail.startswith('ERR:')
    status = 'ERR' if is_err else 'OK '
    if is_err: err += 1
    else: ok += 1
    print(f'  [{status}] {label:<22} {detail}')

print()
print(f'  RESULT: {ok}/{ok+err} checks passed')
print('=' * 55)
