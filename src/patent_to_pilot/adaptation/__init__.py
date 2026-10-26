"""Bounded, explicit-ID project adaptation for the offline G11 slice."""

from .engine import DependencyGuidedAdapter, write_reports
from .models import AdaptationInput, AdaptationReport, ChangeEvent, DependencyGraph

__all__ = ["AdaptationInput", "AdaptationReport", "ChangeEvent", "DependencyGraph", "DependencyGuidedAdapter", "write_reports"]
