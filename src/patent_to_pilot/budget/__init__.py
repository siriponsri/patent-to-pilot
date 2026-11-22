"""Shared budget accounting for every paid model call (research callers and the Workbench).

Use ``from patent_to_pilot.budget.ledger import BudgetLedger, BudgetRefused, shared_ledger``. The package does not
import the module eagerly, so ``python -m patent_to_pilot.budget.ledger`` runs cleanly. Stdlib only.
"""
