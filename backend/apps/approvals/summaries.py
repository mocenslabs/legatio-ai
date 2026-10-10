"""
Human-readable summary generation for approval requests.

Generates clear, actionable summaries that help users understand
why approval is needed and what the proposal entails.

Source: 04-BUSINESS-FLOW.md Section 9.2
"""

from apps.proposals.models import PolicyDecision, Proposal


def generate_approval_summary(
    proposal: Proposal,
    policy_decision: PolicyDecision,
) -> str:
    """
    Generate a human-readable summary for an approval request.

    Args:
        proposal: The proposal requiring approval.
        policy_decision: The policy decision explaining why approval is needed.

    Returns:
        A human-readable summary string.
    """
    parts = []

    # Header
    parts.append("⚠️ Approval Required")
    parts.append("")

    # Proposal details
    if proposal.action_type == "purchase":
        parts.append(f"Your agent negotiated a {proposal.terms.get('destination', 'item')}")
        if proposal.amount:
            parts.append(f"for €{proposal.amount:.2f}")
        if proposal.terms.get("nights"):
            parts.append(f"for {proposal.terms['nights']} nights")
    elif proposal.action_type == "subscribe":
        parts.append("Your agent negotiated a subscription")
        if proposal.amount:
            parts.append(f"for €{proposal.amount:.2f}/month")
        if proposal.contract_length_months:
            parts.append(f"for {proposal.contract_length_months} months")
    else:
        parts.append(f"Your agent proposed a {proposal.action_type}")
        if proposal.amount:
            parts.append(f"for €{proposal.amount:.2f}")

    parts.append("")

    # Policy decision reason
    parts.append("Details:")
    parts.append(f"  Reason: {policy_decision.reason}")
    parts.append(f"  Risk level: {policy_decision.risk_level}")

    # Matched rules
    if policy_decision.matched_rules:
        parts.append(f"  Matched rules: {len(policy_decision.matched_rules)}")
        for rule in policy_decision.matched_rules[:3]:  # Show first 3
            parts.append(f"    - Rule #{rule.get('rule_number')}: {rule.get('name')}")

    # Data fields
    if proposal.data_fields_requested:
        parts.append(f"  Data requested: {', '.join(proposal.data_fields_requested)}")
    else:
        parts.append("  Data requested: None ✓")

    parts.append("")
    parts.append("Decision required: Human approval")

    return "\n".join(parts)


def generate_rejection_summary(
    proposal: Proposal,
    policy_decision: PolicyDecision,
) -> str:
    """
    Generate a summary for a rejected proposal.

    Args:
        proposal: The rejected proposal.
        policy_decision: The policy decision explaining why it was rejected.

    Returns:
        A human-readable summary string.
    """
    parts = []

    parts.append("❌ Proposal Rejected")
    parts.append("")
    parts.append(f"Reason: {policy_decision.reason}")
    parts.append(f"Risk level: {policy_decision.risk_level}")

    if proposal.amount:
        parts.append(f"Amount: €{proposal.amount:.2f}")

    if proposal.data_fields_requested:
        parts.append(f"Data requested: {', '.join(proposal.data_fields_requested)}")

    return "\n".join(parts)
