"""The public package excludes observational records and model weights."""
from pathlib import Path
from scripts.release_gate import check

ROOT = Path(__file__).resolve().parents[1]

def test_full_empirical_gate_requires_original_inputs():
    result = check()
    assert result['status'] == 'NOT_READY_FOR_FULL_EMPIRICAL_RELEASE'
    assert any('data/manifests/' in x for x in result['blockers'])

def test_code_only_distribution_excludes_experimental_records():
    assert not (ROOT/'data').exists()
    assert not (ROOT/'checkpoints').exists()
    assert not (ROOT/'tests/fixtures').exists()
    assert not (ROOT/'docs/TEST_INPUT_PREVIEW.html').exists()

def test_license_file_present():
    assert (ROOT/'LICENSE').exists()
