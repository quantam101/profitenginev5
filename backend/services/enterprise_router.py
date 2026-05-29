"""Enterprise blueprint endpoints — autonomy levels, lifelong catch & correct,
enterprise manifest. Mounted from server.py via app.include_router().
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel


AUTONOMY_LEVELS = {
    "L0": {"mode": "Advisory", "meaning": "AI recommends only"},
    "L1": {"mode": "Drafting", "meaning": "AI creates drafts for approval"},
    "L2": {"mode": "Supervised Automation", "meaning": "AI executes approved workflows"},
    "L3": {"mode": "Bounded Autonomy", "meaning": "AI acts inside rules, budgets, and permissions"},
    "L4": {"mode": "Enterprise Autonomy", "meaning": "AI coordinates agents with logs, controls, escalation"},
    "L5": {"mode": "Restricted Full Autonomy", "meaning": "AI executes low-risk tasks without approval"},
}

# Static seed for Lifelong Catch & Correct — real entries flow in from agents.
_LIFELONG_SEED = [
    {
        "id": "lcc_001",
        "detected_issue": "Stream-B (Amazon Affiliates) CTR dropped 38% week-over-week",
        "root_cause": "Affiliate link decoration broke on three top blog posts after a publisher CMS schema change",
        "business_impact": "Estimated $480/week revenue loss; compounding if uncorrected",
        "recommended_correction": "Patch affiliate-link agent to inspect anchor schema before injection; backfill 3 posts",
        "assigned_agent": "Affiliate Link Agent",
        "risk_level": "medium",
        "expected_improvement": "Restore CTR to baseline 4.1%; recoup $480/week",
        "status": "in_progress",
        "result_after_correction": None,
        "detected_at": "21m ago",
    },
    {
        "id": "lcc_002",
        "detected_issue": "Faceless Video Agent attempted unauthorized $4.00 ElevenLabs call",
        "root_cause": "Voice-style flag missing from policy DSL; cheap fallback not declared",
        "business_impact": "Would have breached $0/mo fixed-cost guardrail",
        "recommended_correction": "Cost Guard escalated to Audit Agent; policy DSL updated to enforce local-TTS fallback",
        "assigned_agent": "Cost Guard Agent",
        "risk_level": "high",
        "expected_improvement": "Zero unauthorized paid actions per cycle",
        "status": "corrected",
        "result_after_correction": "0 unauthorized paid actions in 24h since fix",
        "detected_at": "38m ago",
    },
    {
        "id": "lcc_003",
        "detected_issue": "Proposal Engine reply rate at 6.2% — below 12% target",
        "root_cause": "Cold proposals missing customized capability statement per opportunity",
        "business_impact": "Sales pipeline conversion bottleneck; ~3 deals/mo lost",
        "recommended_correction": "Wire Offer Engineering to enrich each proposal with H&M proof block before send",
        "assigned_agent": "Offer Engineering Agent",
        "risk_level": "medium",
        "expected_improvement": "Lift reply rate to 12%+",
        "status": "queued",
        "result_after_correction": None,
        "detected_at": "1h ago",
    },
    {
        "id": "lcc_004",
        "detected_issue": "Distillation cache hit rate plateaued at 45%",
        "root_cause": "Semantic compressor not deduping near-identical prompts when whitespace differs",
        "business_impact": "Spending ~$0.12/day more than necessary on Claude calls",
        "recommended_correction": "Add lowercase + whitespace-normalize step before hash; reindex cache keys",
        "assigned_agent": "Codex Optimization Agent",
        "risk_level": "low",
        "expected_improvement": "Lift cache hit rate to 65%+; save ~$3/mo",
        "status": "in_progress",
        "result_after_correction": None,
        "detected_at": "3h ago",
    },
]


class AutonomySet(BaseModel):
    level: Literal["L0", "L1", "L2", "L3", "L4", "L5"]


def build_router(db: AsyncIOMotorDatabase) -> APIRouter:
    router = APIRouter()

    # ── Autonomy level ──
    @router.get("/api/autonomy")
    async def get_autonomy() -> dict:
        doc = await db.autonomy_state.find_one({"_id": "current"})
        level = (doc or {}).get("level", "L3")
        return {
            "level": level,
            **AUTONOMY_LEVELS[level],
            "levels": AUTONOMY_LEVELS,
            "approval_required_for": [
                "spending_money", "sending_bulk_outreach", "signing_contracts",
                "changing_payment_systems", "deploying_to_production",
                "accessing_sensitive_data", "modifying_security_controls",
                "training_models_on_private_data",
            ],
        }

    @router.put("/api/autonomy")
    async def set_autonomy(body: AutonomySet) -> dict:
        await db.autonomy_state.update_one(
            {"_id": "current"},
            {"$set": {"level": body.level,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        return {"level": body.level, **AUTONOMY_LEVELS[body.level]}

    # ── Lifelong Catch & Correct ──
    @router.get("/api/lifelong/issues")
    async def list_lifelong_issues(limit: int = 50) -> list[dict]:
        if limit < 1 or limit > 200:
            raise HTTPException(status_code=400, detail="limit must be 1..200")
        persisted = await db.lifelong_issues.find().sort("detected_at", -1).to_list(length=limit)
        for r in persisted:
            r.pop("_id", None)
        return [*persisted, *_LIFELONG_SEED][:limit]

    # ── Enterprise manifest ──
    @router.get("/api/enterprise/manifest")
    async def manifest() -> dict:
        return {
            "system": {
                "name": "ProfitEngineV5",
                "mode": "enterprise_controlled_autonomy",
                "architecture": "parallel_multi_agent",
                "objective": "revenue_capacity_optimization",
                "north_star_target": "1,000,000 USD/day revenue capacity",
                "autonomy_level": "L3",
                "security_model": "zero_trust_hardened",
                "deployment_standard": "production_grade",
                "audit_required": True,
            },
            "objectives": {
                "primary": [
                    "increase_collected_cash", "increase_profitable_revenue",
                    "improve_conversion_rate", "improve_average_order_value",
                    "increase_recurring_revenue", "improve_fulfillment_capacity",
                    "reduce_execution_friction", "create_reusable_assets",
                    "improve_learning_velocity", "improve_operational_efficiency",
                ],
                "blocked": [
                    "fraud", "scams", "spam", "fake_income_guarantees",
                    "illegal_scraping", "exposed_api_keys", "reckless_spending",
                    "unsafe_financial_claims", "unapproved_production_deployments",
                    "private_data_training_without_permission",
                ],
            },
            "revenue_equation": (
                "Daily Revenue = Qualified Demand × Conversion Rate × "
                "Average Order Value × Purchase Frequency × Fulfillment Capacity × Profit Margin"
            ),
            "loop": [
                "Define mission", "Assign parallel agents", "Execute approved actions",
                "Measure outcomes", "Detect bottlenecks", "Analyze failures",
                "Learn missing knowledge", "Distill lessons into rules",
                "Patch systems", "Repeat with higher efficiency",
            ],
        }

    return router
