"""Derive private query outcomes from typed selection, never caller rankings."""
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_outcomes import ARMS, finalize_query


def selection_outcome(output):
    exact_fields(output, {'format', 'query_id', 'binding', 'acquisition_output_sha256', 'result'})
    if output['format'] != 'sacr-selection-stage-v1' or type(output['result']) is not dict:
        raise InputBoundaryError('typed selection output required')
    arms = output['result'].get('arms')
    exact_fields(arms, set(ARMS))
    rankings = {}
    for arm, rows in arms.items():
        if type(rows) is not list or any(type(row) is not dict or 'family_id' not in row for row in rows):
            raise InputBoundaryError('invalid typed selection ranking rows')
        rankings[arm] = [row['family_id'] for row in rows]
    return finalize_query(query_id=output['query_id'], state='READY', arms=rankings)
