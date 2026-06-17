"""Unit tests for Agent Health Monitor

Demonstrates all capabilities:
- 19 component health monitoring
- Weighted health score calculation
- Comprehensive reporting
- Background monitoring loop
- Alert generation
"""

import asyncio
import unittest
from agent_health_monitor import (
    AgentHealthMonitor,
    ComponentHealth,
    ComponentStatus,
    ComponentPriority,
    HealthReport,
    check_agent_health,
)


class TestAgentHealthMonitor(unittest.TestCase):
    """Test suite for AgentHealthMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = AgentHealthMonitor(update_interval_sec=10)

    def test_initialization(self):
        """Test monitor initialization with 19 components."""
        self.assertEqual(len(self.monitor.component_health), 19)
        self.assertEqual(self.monitor.update_interval_sec, 10)

        # Verify all components are initialized
        for comp_id, comp_name, priority in AgentHealthMonitor.COMPONENTS:
            self.assertIn(comp_id, self.monitor.component_health)
            comp = self.monitor.component_health[comp_id]
            self.assertEqual(comp.component_id, comp_id)
            self.assertEqual(comp.component_name, comp_name)
            self.assertEqual(comp.priority, priority)

    def test_component_status_enum(self):
        """Test ComponentStatus enum."""
        statuses = [
            ComponentStatus.HEALTHY,
            ComponentStatus.DEGRADED,
            ComponentStatus.UNHEALTHY,
            ComponentStatus.UNKNOWN,
        ]
        self.assertEqual(len(statuses), 4)

    def test_component_priority_weights(self):
        """Test component priority weight calculations."""
        critical = ComponentHealth(
            "test_critical",
            "Test Critical",
            ComponentStatus.HEALTHY,
            ComponentPriority.CRITICAL,
        )
        important = ComponentHealth(
            "test_important",
            "Test Important",
            ComponentStatus.HEALTHY,
            ComponentPriority.IMPORTANT,
        )
        normal = ComponentHealth(
            "test_normal",
            "Test Normal",
            ComponentStatus.HEALTHY,
            ComponentPriority.NORMAL,
        )

        self.assertAlmostEqual(critical.get_priority_weight(), 0.40)
        self.assertAlmostEqual(important.get_priority_weight(), 0.35)
        self.assertAlmostEqual(normal.get_priority_weight(), 0.25)

    def test_health_score_calculation(self):
        """Test weighted health score calculation."""
        # Create test components
        components = [
            ComponentHealth(
                "c1",
                "Critical 1",
                ComponentStatus.HEALTHY,
                ComponentPriority.CRITICAL,
                health_score=100.0,
            ),
            ComponentHealth(
                "c2",
                "Important 1",
                ComponentStatus.HEALTHY,
                ComponentPriority.IMPORTANT,
                health_score=80.0,
            ),
            ComponentHealth(
                "c3",
                "Normal 1",
                ComponentStatus.HEALTHY,
                ComponentPriority.NORMAL,
                health_score=60.0,
            ),
        ]

        score = self.monitor.calc_score(components)
        # Expected: 100*0.40 + 80*0.35 + 60*0.25 = 40 + 28 + 15 = 83
        expected = 83.0
        self.assertAlmostEqual(score, expected, places=1)

    def test_health_score_empty_list(self):
        """Test health score calculation with empty component list."""
        score = self.monitor.calc_score([])
        self.assertEqual(score, 0.0)

    def test_component_health_dict_conversion(self):
        """Test ComponentHealth to dict conversion."""
        comp = ComponentHealth(
            "test_id",
            "Test Component",
            ComponentStatus.HEALTHY,
            ComponentPriority.CRITICAL,
            health_score=95.0,
            error_count=5,
        )

        comp_dict = comp.to_dict()
        self.assertEqual(comp_dict["component_id"], "test_id")
        self.assertEqual(comp_dict["component_name"], "Test Component")
        self.assertEqual(comp_dict["status"], "healthy")
        self.assertEqual(comp_dict["priority"], "critical")
        self.assertEqual(comp_dict["health_score"], 95.0)
        self.assertEqual(comp_dict["error_count"], 5)

    def test_health_report_dict_conversion(self):
        """Test HealthReport to dict conversion."""
        report = HealthReport(
            overall_health_score=85.5,
            status=ComponentStatus.HEALTHY,
            total_components=19,
            healthy_count=15,
            degraded_count=4,
        )

        report_dict = report.to_dict()
        self.assertEqual(report_dict["overall_health_score"], 85.5)
        self.assertEqual(report_dict["status"], "healthy")
        self.assertEqual(report_dict["total_components"], 19)
        self.assertIn("timestamp", report_dict)
        self.assertIn("critical_alerts", report_dict)
        self.assertIn("warning_alerts", report_dict)

    def test_async_health_check(self):
        """Test asynchronous health check method."""

        async def run_check():
            report = await self.monitor.check_health()
            self.assertIsNotNone(report)
            self.assertEqual(report.total_components, 19)
            self.assertGreater(report.overall_health_score, 0)
            self.assertLessEqual(report.overall_health_score, 100)

        asyncio.run(run_check())

    def test_health_report_generation(self):
        """Test health report generation after check."""

        async def run_check():
            await self.monitor.check_health()
            report = self.monitor.last_report
            self.assertIsNotNone(report)
            self.assertEqual(len(report.component_health), 19)

        asyncio.run(run_check())

    def test_report_output_text_format(self):
        """Test text format health report."""

        async def run_check():
            await self.monitor.check_health()
            report = self.monitor.report(detailed=True, json_format=False)
            self.assertIsInstance(report, str)
            self.assertIn("AGENT HEALTH MONITOR REPORT", report)
            self.assertIn("OVERALL STATUS", report)
            self.assertIn("COMPONENT SUMMARY", report)
            self.assertIn("Health Score:", report)

        asyncio.run(run_check())

    def test_report_output_json_format(self):
        """Test JSON format health report."""
        import json

        async def run_check():
            await self.monitor.check_health()
            report_str = self.monitor.report(detailed=True, json_format=True)
            report_dict = json.loads(report_str)
            self.assertEqual(report_dict["total_components"], 19)
            self.assertIn("overall_health_score", report_dict)
            self.assertIn("component_health", report_dict)

        asyncio.run(run_check())

    def test_monitoring_thread_lifecycle(self):
        """Test starting and stopping background monitoring."""
        self.assertFalse(self.monitor.monitoring_active)
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring_active)

        # Wait for at least one update
        asyncio.run(asyncio.sleep(0.1))

        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring_active)

    def test_health_snapshot_without_update(self):
        """Test getting health snapshot before any update."""
        snapshot = self.monitor.get_health_snapshot()
        self.assertIsNone(snapshot)

    def test_component_health_retrieval(self):
        """Test retrieving individual component health."""
        comp = self.monitor.get_component_health("api_gateway")
        self.assertIsNotNone(comp)
        self.assertEqual(comp.component_id, "api_gateway")
        self.assertEqual(comp.component_name, "API Gateway")

    def test_invalid_component_health_retrieval(self):
        """Test retrieving non-existent component."""
        comp = self.monitor.get_component_health("nonexistent")
        self.assertIsNone(comp)

    def test_component_count(self):
        """Test that exactly 19 components are monitored."""
        self.assertEqual(len(AgentHealthMonitor.COMPONENTS), 19)
        component_ids = [c[0] for c in AgentHealthMonitor.COMPONENTS]
        self.assertEqual(len(set(component_ids)), 19)  # All unique

    def test_alert_generation(self):
        """Test critical and warning alert generation."""

        async def run_check():
            await self.monitor.check_health()
            report = self.monitor.last_report
            self.assertIsNotNone(report)
            # Report should have lists for alerts
            self.assertIsInstance(report.critical_alerts, list)
            self.assertIsInstance(report.warning_alerts, list)

        asyncio.run(run_check())

    def test_trend_calculation(self):
        """Test trend calculation from health history."""

        async def run_multiple_checks():
            # Run multiple checks to build history
            for _ in range(3):
                await self.monitor.check_health()
                await asyncio.sleep(0.01)

            report = self.monitor.last_report
            self.assertIn(
                report.trend, ["stable", "improving", "degrading"]
            )

        asyncio.run(run_multiple_checks())

    def test_uptime_percentage(self):
        """Test uptime percentage calculation."""

        async def run_check():
            await self.monitor.check_health()
            report = self.monitor.last_report
            self.assertIsNotNone(report)
            self.assertGreaterEqual(report.uptime_percentage, 0)
            self.assertLessEqual(report.uptime_percentage, 100)

        asyncio.run(run_check())


class TestCheckAgentHealthFunction(unittest.TestCase):
    """Test the standalone check_agent_health function."""

    def test_quick_health_check(self):
        """Test quick one-off health check function."""

        async def run_check():
            report = await check_agent_health(update_interval=10)
            self.assertIsNotNone(report)
            self.assertEqual(report.total_components, 19)
            self.assertGreater(report.overall_health_score, 0)

        asyncio.run(run_check())


if __name__ == "__main__":
    unittest.main()
