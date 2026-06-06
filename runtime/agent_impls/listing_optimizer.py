from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from runtime.agents import AgentExecution
from runtime.profitability import listing_optimization_rules

LISTINGS_CSV = Path("datacenter/pod_factory/etsy_shop_pack/etsy_listings.csv")


class Agent:
    id = "listing-optimizer"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        rows = []
        if LISTINGS_CSV.exists():
            with LISTINGS_CSV.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        issues = []
        for row in rows:
            tags = [tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()]
            if len(tags) < 13:
                issues.append({"sku": row.get("sku"), "issue": "fewer_than_13_tags"})
            if len(row.get("title", "")) < 40:
                issues.append({"sku": row.get("sku"), "issue": "title_too_short"})
        output = {
            "objective": objective,
            "listings_checked": len(rows),
            "issues": issues,
            "rules": listing_optimization_rules(),
        }
        return AgentExecution(
            output="LISTING_OPTIMIZER_RESULT\n" + json.dumps(output, indent=2),
            metrics={"agent": self.id, "listings_checked": len(rows), "issues": len(issues)},
        )
