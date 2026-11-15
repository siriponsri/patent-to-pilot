"""Paper 1 S8 test configurations: the settled full-dev configuration files with ONLY the stage and batching changed
(test freeze manifest paper1-freeze/test-freeze-manifest.json). Shared by the S8 freeze helpers."""
import copy, json
from takeover_lib import A, document_hash

TEST_INPUT = '/home/chaw/patent-to-pilot-jobs/ptp-paper1-test-inputs-20261115-v1/queries-ta.jsonl'
TEST_SHA = '289cdc311e0a5ecb5e3f3b443a5139f218eb9261255a3fed8638fdbb45eadc59'
TEST_N = 773
BATCH = {'FA': 158, 'GR': 158, 'SACR': 79}
BATCHES = {'FA': 5, 'GR': 5, 'SACR': 10}
ORDER = [(a, b) for a in ('FA', 'GR', 'SACR') for b in range(1, BATCHES[a] + 1)]
SOURCE = {'FA': 'paper1-s4-fa-b3', 'GR': 'paper1-s4-gr-b3', 'SACR': 'sacr-fulldev-b6', 'RET': 'paper1-s5-retrieval'}
BATCHING = {'FA': '773 test queries in pinned file order, 5 batches (4 x 158 + 141)',
            'GR': '773 test queries in pinned file order, 5 batches (4 x 158 + 141)',
            'SACR': '773 test queries in pinned file order, 10 batches (9 x 79 + 62)'}
ENVELOPE = {'test': {'seconds': 10800, 'maximum_calls': 158}}


def job(arm, b):
    return ('ptp-auto-native-sacr-test-b%d-20261115-v1' % b if arm == 'SACR'
            else 'ptp-auto-paper1-%s-test-b%d-20261115-v1' % (arm.lower(), b))


def rows(arm, b):
    start = BATCH[arm] * (b - 1)
    return start, min(BATCH[arm], TEST_N - start)


def configuration(kind):
    dev = json.loads((A/SOURCE[kind]/'configuration.json').read_bytes())
    assert dev['stage'] == 'full_dev'
    c = copy.deepcopy(dev); c['stage'] = 'test'
    c['derived_from_full_dev_configuration_sha256'] = document_hash(dev)
    c['test_freeze_manifest_sha256'] = document_hash(json.loads((A/'paper1-freeze/test-freeze-manifest.json').read_bytes()))
    if kind == 'RET':
        c['protocol'] = c['protocol'].replace('S5', 'S8')
    else:
        c['batching'] = BATCHING[kind]
    return c
