"""Private per-case output on owner-local storage, separate from money accounting.

No credentials or input messages enter this sink. Model output is untrusted data.
A partial file is evidence to inspect, never permission to replay a paid call.
"""
from datetime import datetime, timezone
import json
import os
import re
from .local_epoch import registry_path


class PrivateCaseJournal:
    def __init__(self, run_id):
        if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
            raise ValueError('safe unique run ID required for private output')
        self.path = registry_path().parent.parent / 'evidence' / 'api-generation' / (run_id + '.jsonl')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.locator = 'local-healthtech/evidence/api-generation/' + self.path.name
        self._file = self.path.open('x', encoding='utf-8', newline='\n')
        try:
            self._append({'format':'ptp-private-api-case-journal-v1', 'run_id':run_id,
                'created_utc':datetime.now(timezone.utc).isoformat(), 'private_local_only':True})
        except BaseException:
            self._file.close()
            raise

    def _append(self, record):
        # Serialize fully before writing, then flush to disk before returning.
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False)
        self._file.write(line + '\n')
        self._file.flush()
        os.fsync(self._file.fileno())

    def write(self, case):
        # Explicit output fields only: no request, input messages, key, config
        # dump or raw exception. Received invalid model text is still evidence.
        allowed = {'case_id','attempt_id','message_sha256','payload_sha256','wire_payload_sha256',
            'input_token_bound','schema_framing_token_bound','output_token_bound','cost_upper_bound_usd',
            'status','error_class','schema_valid','elapsed_seconds','latency_seconds','output_text',
            'output_sha256','parsed_output','usage','cost_usd','actual_debit_usd','billing_state',
            'provider_generation_id','reported_model','reported_upstream_provider'}
        self._append({'recorded_utc':datetime.now(timezone.utc).isoformat(),
            'case':{key:value for key,value in case.items() if key in allowed}})

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._file.close()
