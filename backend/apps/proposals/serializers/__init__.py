"""Proposals serializers.

This module exports all serializers from the proposals app.
"""

from apps.proposals.serializers.proposal import (
    ProposalCreateSerializer,
    ProposalDetailSerializer,
    ProposalSerializer,
)

__all__ = ["ProposalCreateSerializer", "ProposalDetailSerializer", "ProposalSerializer"]
