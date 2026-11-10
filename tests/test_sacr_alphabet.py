import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_alphabet import build_alphabet


class Tokenizer:
    def __len__(self):
        return 3

    def decode(self, ids, **kwargs):
        assert kwargs == {'skip_special_tokens': False}
        return ['ไทย', '🧪', '\n\t'][ids[0]]


def test_vocabulary_and_unseen_source_scalars_preserved_deterministically():
    a = build_alphabet(Tokenizer(), 'source Ω\n')
    assert set('ไทย🧪Ω\\"') <= set(a['alphabet'])
    assert '\n' not in a['alphabet']
    assert a == build_alphabet(Tokenizer(), 'source Ω\n')
    assert a['alphabet'] == ''.join(sorted(set(a['alphabet'])))


@pytest.mark.parametrize('source', ['', ' ', '\ud800'])
def test_invalid_source_refused(source):
    with pytest.raises(InputBoundaryError):
        build_alphabet(Tokenizer(), source)
