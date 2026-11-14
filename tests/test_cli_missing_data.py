"""Strict scientific verification must not succeed without source measurements."""
import subprocess,sys,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
def test_missing_measurements_cannot_be_published_as_verified(tmp_path):
    p=subprocess.run([sys.executable,str(ROOT/'scripts'/'recompute_experiments.py'),
        '--inputs',str(tmp_path), '--output',str(tmp_path/'out.json'),'--strict'],capture_output=True,text=True)
    assert p.returncode==2
    assert json.loads((tmp_path/'out.json').read_text())['status']=='INCOMPLETE'
