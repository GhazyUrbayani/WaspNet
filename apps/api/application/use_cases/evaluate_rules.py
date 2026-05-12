"""
ChainRadar — Alert Rule Evaluator (Use Case)
Pure function — evaluates wallet data against alert conditions.
ARCH: No side effects, fully unit testable, TDD-first.
"""

import structlog
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = structlog.get_logger()


class EvaluationResult:
    """Result of evaluating a single alert rule."""

    def __init__(
        self,
        rule_id: str,
        triggered: bool,
        matched_conditions: List[Dict[str, Any]],
        severity: str = "info",
        summary: str = "",
    ):
        self.rule_id = rule_id
        self.triggered = triggered
        self.matched_conditions = matched_conditions
        self.severity = severity
        self.summary = summary
        self.evaluated_at = datetime.utcnow()


def evaluate_rules(
    rules: List[Dict[str, Any]],
    wallet_data: Dict[str, Any],
    event_data: Optional[Dict[str, Any]] = None,
) -> List[EvaluationResult]:
    """
    Evaluate a list of alert rules against wallet data.

    Args:
        rules: List of alert rule dicts with conditions
        wallet_data: Current wallet state (balances, etc.)
        event_data: Optional event from SIM webhook

    Returns:
        List of EvaluationResult for rules that triggered
    """
    results = []

    for rule in rules:
        result = _evaluate_single_rule(rule, wallet_data, event_data)
        if result.triggered:
            results.append(result)

    return results


def _evaluate_single_rule(
    rule: Dict[str, Any],
    wallet_data: Dict[str, Any],
    event_data: Optional[Dict[str, Any]] = None,
) -> EvaluationResult:
    """Evaluate a single rule — ALL conditions must match (AND logic)."""
    conditions = rule.get("conditions", [])
    matched = []

    for condition in conditions:
        cond_type = condition.get("condition_type", "")
        threshold = condition.get("threshold", 0)
        comparison = condition.get("comparison", "gte")

        is_match = False
        match_detail = {}

        if cond_type == "balance_above":
            balance = _extract_sol_balance(wallet_data)
            is_match = _compare(balance, threshold, comparison)
            match_detail = {"balance": balance, "threshold": threshold}

        elif cond_type == "balance_below":
            balance = _extract_sol_balance(wallet_data)
            is_match = _compare(balance, threshold, "lte")
            match_detail = {"balance": balance, "threshold": threshold}

        elif cond_type == "balance_change":
            change_pct = _calculate_balance_change(wallet_data, event_data)
            is_match = abs(change_pct) >= threshold
            match_detail = {"change_percent": change_pct, "threshold": threshold}

        elif cond_type == "large_transfer":
            transfer_amount = _extract_transfer_amount(event_data)
            is_match = _compare(transfer_amount, threshold, comparison)
            match_detail = {"transfer_amount": transfer_amount, "threshold": threshold}

        elif cond_type == "whale_movement":
            transfer_amount = _extract_transfer_amount(event_data)
            is_match = transfer_amount >= threshold
            match_detail = {"transfer_amount": transfer_amount, "whale_threshold": threshold}

        elif cond_type == "token_transfer":
            token_mint = condition.get("token_mint", "")
            token_amount = _extract_token_transfer(event_data, token_mint)
            is_match = _compare(token_amount, threshold, comparison)
            match_detail = {"token_mint": token_mint, "amount": token_amount}

        elif cond_type == "new_token":
            is_match = _detect_new_token(event_data)
            match_detail = {"new_token_detected": is_match}

        elif cond_type == "program_interaction":
            program_id = condition.get("program_id", "")
            is_match = _detect_program_interaction(event_data, program_id)
            match_detail = {"program_id": program_id}

        if is_match:
            matched.append({
                "condition_type": cond_type,
                "detail": match_detail,
            })

    # AND logic: all conditions must match
    triggered = len(matched) == len(conditions) and len(conditions) > 0

    summary = ""
    if triggered:
        summaries = [f"{m['condition_type']}: {m['detail']}" for m in matched]
        summary = " AND ".join(summaries)

    return EvaluationResult(
        rule_id=rule.get("id", ""),
        triggered=triggered,
        matched_conditions=matched,
        severity=rule.get("severity", "info"),
        summary=summary,
    )


def _compare(value: float, threshold: float, comparison: str) -> bool:
    """Compare value against threshold using comparison operator."""
    ops = {
        "gte": lambda v, t: v >= t,
        "lte": lambda v, t: v <= t,
        "gt": lambda v, t: v > t,
        "lt": lambda v, t: v < t,
        "eq": lambda v, t: abs(v - t) < 0.0001,
    }
    return ops.get(comparison, ops["gte"])(value, threshold)


def _extract_sol_balance(wallet_data: Dict) -> float:
    """Extract SOL balance from wallet data (in SOL, not lamports)."""
    balances = wallet_data.get("balances", wallet_data)
    if isinstance(balances, dict):
        lamports = balances.get("lamports", balances.get("balance", 0))
        if isinstance(lamports, (int, float)) and lamports > 1_000_000:
            return lamports / 1_000_000_000  # Convert lamports to SOL
        return float(lamports)
    return 0.0


def _calculate_balance_change(wallet_data: Dict, event_data: Optional[Dict]) -> float:
    """Calculate percentage change in balance."""
    if not event_data:
        return 0.0
    prev = event_data.get("previous_balance", 0)
    curr = event_data.get("current_balance", _extract_sol_balance(wallet_data))
    if prev == 0:
        return 100.0 if curr > 0 else 0.0
    return ((curr - prev) / prev) * 100


def _extract_transfer_amount(event_data: Optional[Dict]) -> float:
    """Extract transfer amount from event data (in SOL)."""
    if not event_data:
        return 0.0
    amount = event_data.get("amount", event_data.get("transfer_amount", 0))
    if isinstance(amount, (int, float)) and amount > 1_000_000:
        return amount / 1_000_000_000
    return float(amount)


def _extract_token_transfer(event_data: Optional[Dict], token_mint: str) -> float:
    """Extract specific token transfer amount."""
    if not event_data:
        return 0.0
    transfers = event_data.get("token_transfers", [])
    for t in transfers:
        if t.get("mint", "") == token_mint:
            return float(t.get("amount", 0))
    return 0.0


def _detect_new_token(event_data: Optional[Dict]) -> bool:
    """Detect if event represents a new token appearing."""
    if not event_data:
        return False
    return event_data.get("type") == "token_transfer" and event_data.get("is_new_token", False)


def _detect_program_interaction(event_data: Optional[Dict], program_id: str) -> bool:
    """Detect interaction with a specific program."""
    if not event_data:
        return False
    programs = event_data.get("program_ids", [])
    return program_id in programs
