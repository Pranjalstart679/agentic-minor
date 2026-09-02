"""
Unit test for Hybrid Agent Orchestrator.
"""

from src.orchestrator.hybrid_pipeline import HybridOrchestrator, OrchestrationResult


def test_hybrid_orchestrator_dry_run():
    orchestrator = HybridOrchestrator()
    result = orchestrator.run_pipeline("Test task", dry_run=True)
    assert isinstance(result, OrchestrationResult)
    assert result.status == "SUCCESS"
    assert "Execution Plan" in result.plan
    assert "execute_task" in result.code
    assert "Verification Passed" in result.review
