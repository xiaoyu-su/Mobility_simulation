import logging

from tools.windowed_eval.runtime import build


def test_initialization_warning_cannot_append_to_the_previous_baseline(tmp_path,monkeypatch,capsys):
    root=logging.getLogger();old_handlers=list(root.handlers);old_level=root.level
    previous=tmp_path/'previous.log'
    handler=logging.FileHandler(previous);root.handlers=[handler];root.setLevel(logging.WARNING)
    expected=object()
    def initialize(parameters):
        logging.warning('current seed initialization')
        return expected
    monkeypatch.setattr('tools.windowed_eval.runtime.load_simulation_environment',initialize)
    try:
        assert build({},tmp_path/'next-run') is expected
        assert previous.read_text()==''
        assert 'current seed initialization' in capsys.readouterr().err
    finally:
        for active in root.handlers:active.close()
        root.handlers=old_handlers;root.setLevel(old_level)
