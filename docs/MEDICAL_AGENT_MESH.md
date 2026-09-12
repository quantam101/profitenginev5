# Medical Logistics Agent Mesh

This subsystem runs locally against Ollama and stores its state in SQLite WAL mode. It does not run inside Vercel.

## Safety model

- Ollama is restricted to loopback URLs.
- Network retrieval is disabled by default.
- SAM.gov access requires `SAM_GOV_API_KEY` and an explicit `MEDICAL_MESH_NETWORK_ENABLED=true`.
- Insurance and driver certifications default to unverified. Missing evidence blocks bidding.
- The system creates outreach drafts only. `MEDICAL_MESH_ALLOW_SEND` is reserved for a separately authenticated sender integration and defaults to false.
- Repeated imports are idempotent using a stable SHA-256 lead fingerprint.

## Local source format

Write verified prospects to `data/medical-opportunities.json` as a JSON array. Each record must contain `company_name`, `category`, and `source_url`. Optional fields are `contact_name`, `contact_role`, `phone`, `email`, `solicitation_id`, `equipment_type`, and `deadline`.

## Windows installation

Run PowerShell as the intended service user:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-medical-agent-mesh.ps1
```

The installer validates Ollama, downloads `qwen2.5:14b`, creates an isolated Python environment, runs a health check, and registers a daily 8:00 AM local-time task.

## Linux installation

Install the two units from `deploy/systemd`, create `/etc/alreadyhere/medical-agent-mesh.env` with permissions `0600`, then run:

```bash
systemctl daemon-reload
systemctl enable --now alreadyhere-medical-agent-mesh.timer
```

## Verified runtime facts

Use environment variables to record evidence-backed coverage only:

```text
COMPANY_AUTO_LIABILITY_USD=0
COMPANY_CARGO_COVERAGE_USD=0
DRIVER_HIPAA_CERTIFIED=false
DRIVER_BBP_CERTIFIED=false
```

Replace zero/false only after the current COI or certificate is verified. Credentials belong in Windows Credential Manager or the root-readable Linux environment file, never in Git.
