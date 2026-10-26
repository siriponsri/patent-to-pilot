import importlib.util
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path
import pytest
from patent_to_pilot.providers import env_file
from patent_to_pilot.providers.pilot import plan_hash

ROOT = Path(__file__).parents[1]
FAKE = 'FAKE_ONLY_NOT_A_REAL_OPENROUTER_KEY'


@pytest.mark.parametrize('text', [
    'OPENROUTER_API_KEY='+FAKE,
    '# comment\r\n\r\n OPENROUTER_API_KEY = '+FAKE+'\r\n',
    '\ufeffOPENROUTER_API_KEY="'+FAKE+'"\n',
    "OPENROUTER_API_KEY='"+FAKE+"'\n",
])
def test_parse_supported_literals(text):
    assert env_file.parse_key(text)==FAKE


@pytest.mark.parametrize('text', [
    'OPENROUTER_API_KEY=',
    'OTHER_KEY='+FAKE,
    'export OPENROUTER_API_KEY='+FAKE,
    'OPENROUTER_API_KEY='+FAKE+'\nOPENROUTER_API_KEY='+FAKE,
    'OPENROUTER_API_KEY="'+FAKE,
    'OPENROUTER_API_KEY='+FAKE+' # inline comment',
    'OPENROUTER_API_KEY="'+FAKE+'\nsecond-line"',
])
def test_invalid_syntax_never_includes_value(text):
    with pytest.raises(env_file.EnvFileError) as result:env_file.parse_key(text)
    assert str(result.value).find(FAKE)==-1


def test_no_interpolation_or_shell_execution():
    assert env_file.parse_key('OPENROUTER_API_KEY="$(whoami)"')=='$(whoami)'
    assert env_file.parse_key('OPENROUTER_API_KEY=${OTHER_SECRET}')=='${OTHER_SECRET}'


def test_missing_and_placeholder_are_explicit():
    for text,code in [('# blank file','ENV_FILE_MISSING_KEY'),('OPENROUTER_API_KEY='+env_file.PLACEHOLDER,'ENV_FILE_PLACEHOLDER')]:
        with pytest.raises(env_file.EnvFileError) as result:env_file.parse_key(text)
        assert result.value.code==code


def test_file_encoding_size_and_unreadable_errors(tmp_path):
    file=tmp_path/'fake-key.env';file.write_bytes(('\ufeffOPENROUTER_API_KEY='+FAKE+'\r\n').encode('utf-8'))
    assert env_file.read_key(file)==FAKE
    file.write_bytes(b'x'*(env_file.MAX_FILE_BYTES+1))
    with pytest.raises(env_file.EnvFileError,match='ENV_FILE_TOO_LARGE'):env_file.read_key(file)
    file.write_bytes(b'\xff\xfe\x00')
    with pytest.raises(env_file.EnvFileError,match='ENV_FILE_UNREADABLE'):env_file.read_key(file)
    missing=tmp_path/FAKE
    try:env_file.read_key(missing)
    except env_file.EnvFileError:
        formatted=traceback.format_exc()
        assert formatted.find(FAKE)==-1 and 'FileNotFoundError' not in formatted


def test_environment_precedence_skips_file_entirely(tmp_path,monkeypatch):
    def forbidden(*a,**k):raise AssertionError('file must not be read')
    monkeypatch.setattr(env_file,'read_key',forbidden)
    env={env_file.KEY_NAME:FAKE}
    with env_file.scoped_env_file_key(tmp_path/'not-used.env',environ=env) as source:
        assert source=='environment' and env[env_file.KEY_NAME]==FAKE
    assert env[env_file.KEY_NAME]==FAKE


@pytest.mark.parametrize('previous',[None,''])
def test_process_value_is_restored_even_when_dispatch_fails(tmp_path,previous):
    file=tmp_path/'fake-key.env';file.write_text('OPENROUTER_API_KEY='+FAKE,encoding='utf-8')
    env={} if previous is None else {env_file.KEY_NAME:previous}
    with pytest.raises(RuntimeError):
        with env_file.scoped_env_file_key(file,environ=env) as source:
            assert source=='env_file' and env[env_file.KEY_NAME]==FAKE
            raise RuntimeError('synthetic dispatch failure')
    assert env==({} if previous is None else {env_file.KEY_NAME:previous})


def cli():
    spec=importlib.util.spec_from_file_location('env_file_cli_under_test',ROOT/'scripts/dispatch_provider_pilot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.mark.parametrize('mock',[False,True])
def test_dry_run_and_mock_do_not_touch_secret_file(tmp_path,monkeypatch,capsys,mock):
    module=cli()
    def forbidden(*a,**k):raise AssertionError('credential loader called')
    monkeypatch.setattr(module,'scoped_env_file_key',forbidden)
    args=[str(ROOT/'scripts/dispatch_provider_pilot.py'),'--env-file',str(tmp_path/'must-not-be-read.env'),'--state',str(tmp_path/'mock.sqlite3')]
    if mock:args.append('--mock')
    monkeypatch.setattr(sys,'argv',args)
    assert module.main()==0
    result=json.loads(capsys.readouterr().out)
    assert result['status']==('PHASE_COMPLETE' if mock else 'READY_AWAITING_FUNDING_AND_BUDGET_APPROVAL')


def auth_file(tmp_path,approved):
    plan=json.loads((ROOT/'configs/provider-pilot-plan.json').read_text(encoding='utf-8'))
    state=tmp_path/'fake-live.sqlite3'
    payload=dict(approved=approved,funding_confirmed=approved,plan_sha256=plan_hash(plan),phase='smoke',phase_spend_cap_usd=.6,phase_attempts_max=2,state_path=str(state.resolve()),owner_reference='FAKE UNIT TEST ONLY')
    approval=tmp_path/'fake-approval.json';approval.write_text(json.dumps(payload),encoding='utf-8')
    return approval,state


def test_unapproved_live_never_reads_key_or_calls_dispatch(tmp_path,monkeypatch,capsys):
    module=cli();approval,state=auth_file(tmp_path,False)
    def forbidden(*a,**k):raise AssertionError('secret or dispatcher accessed before approval')
    monkeypatch.setattr(module,'scoped_env_file_key',forbidden);monkeypatch.setattr(module,'dispatch',forbidden)
    monkeypatch.setattr(sys,'argv',['dispatch','--live','--approval',str(approval),'--state',str(state),'--env-file',str(tmp_path/'no-read.env')])
    assert module.main()==2
    output=capsys.readouterr();assert 'PilotError' in output.err and not state.exists()


def test_approved_fake_dispatch_uses_file_temporarily_and_redacts_failure(tmp_path,monkeypatch,capsys):
    module=cli();approval,state=auth_file(tmp_path,True)
    file=tmp_path/'fake-key.env';file.write_text('OPENROUTER_API_KEY='+FAKE,encoding='utf-8')
    isolated_env={};monkeypatch.setattr(env_file.os,'environ',isolated_env)
    def fake_dispatch(*a,**k):
        assert isolated_env[env_file.KEY_NAME]==FAKE
        raise OSError(FAKE)
    monkeypatch.setattr(module,'dispatch',fake_dispatch)
    monkeypatch.setattr(sys,'argv',['dispatch','--live','--approval',str(approval),'--state',str(state),'--env-file',str(file)])
    assert module.main()==2 and env_file.KEY_NAME not in isolated_env
    output=capsys.readouterr();assert (output.out+output.err).find(FAKE)==-1 and 'Traceback' not in output.err


def test_cli_invalid_file_reports_fixed_code_only(tmp_path,monkeypatch,capsys):
    module=cli();approval,state=auth_file(tmp_path,True)
    file=tmp_path/'fake-key.env';file.write_text('OPENROUTER_API_KEY='+FAKE+' bad value',encoding='utf-8')
    isolated_env={};monkeypatch.setattr(env_file.os,'environ',isolated_env)
    def forbidden(*a,**k):raise AssertionError('must not dispatch with invalid key file')
    monkeypatch.setattr(module,'dispatch',forbidden)
    monkeypatch.setattr(sys,'argv',['dispatch','--live','--approval',str(approval),'--state',str(state),'--env-file',str(file)])
    assert module.main()==2
    output=capsys.readouterr();result=json.loads(output.err)
    assert result['error_code']=='ENV_FILE_INVALID' and output.err.find(FAKE)==-1


def test_git_ignores_real_names_but_keeps_example_trackable(tmp_path):
    # Evaluate public ignore rules in an owned fake repo; do not change global
    # safe.directory or touch the real project's index/credential files.
    subprocess.run(['git','init','--quiet',str(tmp_path)],check=True,capture_output=True)
    (tmp_path/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
    for name in ['.env','.env.local','.env.fake-test-backup']:
        result=subprocess.run(['git','-C',str(tmp_path),'check-ignore','--quiet','--',name],capture_output=True)
        assert result.returncode==0
    result=subprocess.run(['git','-C',str(tmp_path),'check-ignore','--quiet','--','.env.example'],capture_output=True)
    assert result.returncode==1
