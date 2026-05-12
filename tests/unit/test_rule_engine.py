"""
ChainRadar — Unit Tests: Rule Engine
TDD tests for alert condition evaluation.
"""

import pytest
from application.use_cases.evaluate_rules import evaluate_rules, _compare, _extract_sol_balance


class TestCompareFunction:
    """Test the comparison operator function."""

    def test_gte_true(self):
        assert _compare(100, 50, "gte") is True

    def test_gte_equal(self):
        assert _compare(50, 50, "gte") is True

    def test_gte_false(self):
        assert _compare(49, 50, "gte") is False

    def test_lte_true(self):
        assert _compare(30, 50, "lte") is True

    def test_gt_true(self):
        assert _compare(51, 50, "gt") is True

    def test_gt_equal_false(self):
        assert _compare(50, 50, "gt") is False

    def test_lt_true(self):
        assert _compare(49, 50, "lt") is True

    def test_eq_true(self):
        assert _compare(50, 50, "eq") is True

    def test_eq_close_enough(self):
        assert _compare(50.00001, 50.00001, "eq") is True

    def test_unknown_comparison_defaults_to_gte(self):
        assert _compare(100, 50, "unknown") is True


class TestExtractSolBalance:
    """Test SOL balance extraction from various data formats."""

    def test_lamports_conversion(self):
        data = {"lamports": 45_000_000_000}
        assert _extract_sol_balance(data) == 45.0

    def test_direct_balance(self):
        data = {"balance": 100.5}
        assert _extract_sol_balance(data) == 100.5

    def test_nested_balances(self):
        data = {"balances": {"lamports": 10_000_000_000}}
        assert _extract_sol_balance(data) == 10.0

    def test_empty_data(self):
        assert _extract_sol_balance({}) == 0.0


class TestEvaluateRules:
    """Test full rule evaluation pipeline."""

    def test_balance_above_triggered(self):
        rules = [{
            "id": "rule1",
            "conditions": [{"condition_type": "balance_above", "threshold": 100, "comparison": "gte"}],
            "severity": "warning",
        }]
        wallet_data = {"balance": 150}
        results = evaluate_rules(rules, wallet_data)
        assert len(results) == 1
        assert results[0].triggered is True
        assert results[0].rule_id == "rule1"

    def test_balance_above_not_triggered(self):
        rules = [{
            "id": "rule1",
            "conditions": [{"condition_type": "balance_above", "threshold": 200, "comparison": "gte"}],
            "severity": "warning",
        }]
        wallet_data = {"balance": 150}
        results = evaluate_rules(rules, wallet_data)
        assert len(results) == 0

    def test_large_transfer_triggered(self):
        rules = [{
            "id": "rule2",
            "conditions": [{"condition_type": "large_transfer", "threshold": 500, "comparison": "gte"}],
            "severity": "critical",
        }]
        event_data = {"amount": 750}
        results = evaluate_rules(rules, {}, event_data)
        assert len(results) == 1
        assert results[0].severity == "critical"

    def test_multiple_conditions_and_logic(self):
        """All conditions must match (AND logic)."""
        rules = [{
            "id": "rule3",
            "conditions": [
                {"condition_type": "balance_above", "threshold": 100, "comparison": "gte"},
                {"condition_type": "large_transfer", "threshold": 50, "comparison": "gte"},
            ],
            "severity": "warning",
        }]
        wallet_data = {"balance": 200}
        event_data = {"amount": 100}
        results = evaluate_rules(rules, wallet_data, event_data)
        assert len(results) == 1

    def test_partial_conditions_not_triggered(self):
        """If only some conditions match, rule should NOT trigger."""
        rules = [{
            "id": "rule4",
            "conditions": [
                {"condition_type": "balance_above", "threshold": 100, "comparison": "gte"},
                {"condition_type": "large_transfer", "threshold": 500, "comparison": "gte"},
            ],
            "severity": "warning",
        }]
        wallet_data = {"balance": 200}
        event_data = {"amount": 10}  # Below threshold
        results = evaluate_rules(rules, wallet_data, event_data)
        assert len(results) == 0

    def test_empty_rules(self):
        results = evaluate_rules([], {})
        assert results == []

    def test_empty_conditions(self):
        rules = [{"id": "rule5", "conditions": [], "severity": "info"}]
        results = evaluate_rules(rules, {})
        assert len(results) == 0

    def test_whale_movement_triggered(self):
        rules = [{
            "id": "rule6",
            "conditions": [{"condition_type": "whale_movement", "threshold": 1000, "comparison": "gte"}],
            "severity": "critical",
        }]
        event_data = {"amount": 5000}
        results = evaluate_rules(rules, {}, event_data)
        assert len(results) == 1

    def test_balance_change_percentage(self):
        rules = [{
            "id": "rule7",
            "conditions": [{"condition_type": "balance_change", "threshold": 5, "comparison": "gte"}],
            "severity": "warning",
        }]
        event_data = {"previous_balance": 100, "current_balance": 110}
        results = evaluate_rules(rules, {}, event_data)
        assert len(results) == 1  # 10% change > 5% threshold

    def test_new_token_detected(self):
        rules = [{
            "id": "rule8",
            "conditions": [{"condition_type": "new_token", "threshold": 0, "comparison": "gte"}],
            "severity": "info",
        }]
        event_data = {"type": "token_transfer", "is_new_token": True}
        results = evaluate_rules(rules, {}, event_data)
        assert len(results) == 1

    def test_program_interaction(self):
        rules = [{
            "id": "rule9",
            "conditions": [{"condition_type": "program_interaction", "threshold": 0, "comparison": "gte", "program_id": "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcPp7GQFZ"}],
            "severity": "info",
        }]
        event_data = {"program_ids": ["JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcPp7GQFZ"]}
        results = evaluate_rules(rules, {}, event_data)
        assert len(results) == 1
