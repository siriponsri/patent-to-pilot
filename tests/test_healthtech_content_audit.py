from patent_to_pilot.healthtech.content_audit import audit_case

EVIDENCE = [
    {"evidence_id": "E-pma", "source_id": "src-1", "locator": "field:pma_number", "structured_field": "pma_number",
     "structured_value": "P100009", "support_basis": "Supplied source field"},
    {"evidence_id": "E-name", "source_id": "src-1", "locator": "field:trade_name", "structured_field": "trade_name",
     "structured_value": "MITRACLIP DELIVERY SYSTEM", "support_basis": "Supplied source field"},
]
CASE = {"case_id": "C1", "evidence": EVIDENCE, "unresolved_items": [],
        "query": {"device_id_canonical": "P100009:BASE", "device_id_raw": "MITRACLIP DELIVERY SYSTEM (P100009:BASE)"}}


def finding(record_id, summary, locator=None, source_id="src-1", classification="source_fact"):
    row = {r["evidence_id"]: r for r in EVIDENCE}[record_id]
    return {"record_type": "evidence", "record_id": record_id, "source_id": source_id,
            "locator": locator or row["locator"], "classification": classification,
            "summary": summary, "support_basis": "Supplied source field"}


def test_all_correct_and_complete():
    out = {"device_id": "P100009:BASE", "device_name": "MitraClip Delivery System", "unresolved": [],
           "findings": [finding("E-pma", "The PMA number is P100009."),
                        finding("E-name", "Trade name: MITRACLIP DELIVERY SYSTEM.")]}
    r = audit_case(CASE, out)
    assert (r["correct"], r["incorrect_or_unsupported"], r["flagged_other"]) == (2, 0, 0)
    assert r["missing_evidence_ids"] == [] and r["device_id_matches_query"] and r["device_name_supported"]


def test_wrong_value_missing_row_and_inference_are_flagged():
    out = {"device_id": "P100009:BASE", "device_name": "Other device", "unresolved": [],
           "findings": [finding("E-pma", "The PMA number is P100010."),
                        finding("E-pma", "P100009 shows the device is FDA approved and safe.")]}
    r = audit_case(CASE, out)
    labels = [f["label"] for f in r["finding_results"]]
    assert labels == ["incorrect_or_unsupported", "correct_value_with_extra_inference"]
    assert r["missing_evidence_ids"] == ["E-name"]
    assert r["duplicate_citations"] == ["E-pma"]
    assert not r["device_name_supported"]


def test_wrong_locator_and_unknown_record():
    out = {"device_id": "WRONG", "device_name": "MITRACLIP DELIVERY SYSTEM", "unresolved": [],
           "findings": [finding("E-name", "MITRACLIP DELIVERY SYSTEM", locator="field:applicant"),
                        {**finding("E-pma", "P100009"), "record_id": "E-x"}]}
    r = audit_case(CASE, out)
    labels = [f["label"] for f in r["finding_results"]]
    assert labels == ["correct_value_wrong_citation", "unsupported"]
    assert not r["device_id_matches_query"]
