"""Distinct prospective claims; R5's full-source coverage gate is unchanged."""
from .sacr_r6_candidate import CRITERIA as SACR_CRITERIA

RECORD_CRITERIA = {
 'roles_direction':'Judge the proposed positive capability of the claimed device: action, operand, actor and direction must agree with the full source.',
 'quantities_units':'Every quantity/unit needed to interpret a retained claim must be preserved; unrelated unextracted functions belong to coverage reporting.',
 'polarity_exceptions':'A negated capability or exception must not become a positive invention capability.',
 'condition_attachment':'Keep every condition necessary for the retained claim and its attachment. Missing external procedure/context requires uncertainty.',
 'essential_coverage':'Check completeness of each retained claim and its necessary constraints, not coverage of all functions in the family. Empty output is abstention, never fidelity success.',
 'abstraction_support':'The asserted action/operand must remain source-supported; literal spans alone do not establish the role interpretation.',
 'context_preservation':'Do not attribute prior-art/background capabilities to the claimed device. Unavailable external context requires uncertainty.'}
ALIAS_CRITERIA = {
 'roles_direction':'Both witnesses must assert the same positive technical action/operand function, not merely identical words.',
 'quantities_units':'Preserve each witness quantity/unit separately. Different operating ranges alone do not refute this shared-function edge.',
 'polarity_exceptions':'A positive capability and its negation do not establish a shared positive capability.',
 'condition_attachment':'Retain the conditions of each witness separately. Do not assert common operating ranges or interchangeability.',
 'essential_coverage':'Both witnesses and their necessary context must be present; no claim of full-family function coverage is made.',
 'abstraction_support':'Shared function means the same technical action and operand meaning; lexical polysemy is not equivalence.',
 'context_preservation':'Retain full witness context. Missing context needed to resolve meaning requires uncertainty; no device interchangeability is asserted.'}

def criteria(branch):
    return dict({'SACR':SACR_CRITERIA,'SG_RECORD':RECORD_CRITERIA,'SG_ALIAS':ALIAS_CRITERIA}[branch])
