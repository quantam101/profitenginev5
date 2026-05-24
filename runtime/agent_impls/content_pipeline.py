"""
Content Pipeline agent — the full end-to-end automated content loop.

Runs in sequence:
  1. Trend Scanner  — finds hot topics from HN, Reddit, GitHub
  2. Content Gen    — writes a 1,000-1,500 word SEO article via AI
  3. Blog Publisher — publishes to Dev.to + GitHub Pages, sends email

This is the agent to schedule via n8n for daily automated publishing.
One run = one article published across all configured platforms.

Typical cycle time:
  - With Groq (700 tok/s): ~15-25 seconds total
  - With Gemini Flash:      ~20-35 seconds total
  - With Ollama on ARM CPU: ~3-8 minutes total
"""
from __future__ import annotations

import json
from typing import List

from runtime.agent_impls.blog_publisher import Agent as BlogPublisher
from runtime.agent_impls.content_gen import Agent as ContentGen
from runtime.agent_impls.trend_scanner import Agent as TrendScanner
from runtime.agents import AgentExecution


class Agent:
    id = "content-pipeline"

    def run(self, objective: str, context: str, connectors: List[str]) -> AgentExecution:
        topic = objective  # default: use provided objective as the topic

        # ── Step 1: Trend scan (optional — skip if objective is explicit) ──
        trend_result = None
        auto_topic = not any(
            word in objective.lower()
            for word in ["write", "create", "article", "post", "about"]
        )

        if auto_topic:
            scanner = TrendScanner()
            scan = scanner.run("Find the best topic for an affiliate blog post today", "", connectors)
            trend_result = scan.output

            # Extract first topic from trend scanner output
            try:
                start = scan.output.find("[")
                end = scan.output.rfind("]") + 1
                if start >= 0 and end > start:
                    topics = json.loads(scan.output[start:end])
                    if topics:
                        topic = topics[0].get("title", objective)
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        # ── Step 2: Generate content ───────────────────────────────────────
        gen_agent = ContentGen()
        gen_result = gen_agent.run(topic, context, connectors)

        # ── Step 3: Publish ────────────────────────────────────────────────
        pub_agent = BlogPublisher()
        pub_result = pub_agent.run(topic, gen_result.output, connectors)

        # ── Compile final output ───────────────────────────────────────────
        tier = gen_result.metrics.get("tier", "unknown")
        published_count = int(pub_result.metrics.get("published_count", 0))
        word_count = int(gen_result.metrics.get("word_count", 0))

        output_sections = ["CONTENT_PIPELINE_RESULT"]
        if trend_result:
            output_sections.append(f"\n── Trends ──\n{trend_result[:300]}...")
        output_sections.append(f"\n── Content ──\n{gen_result.output[:400]}...")
        output_sections.append(f"\n── Publish ──\n{pub_result.output}")

        return AgentExecution(
            output="\n".join(output_sections),
            metrics={
                "agent": self.id,
                "tier": tier,
                "word_count": word_count,
                "published_count": published_count,
                "platforms": pub_result.metrics.get("platforms", ""),
                "errors": pub_result.metrics.get("errors", 0),
            },
        )
