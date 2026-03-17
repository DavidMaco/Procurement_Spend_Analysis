from types import SimpleNamespace

from procurement_spend_analysis import cli


def test_cli_main_launches_uvicorn_without_starting_server(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(api_port=9123, environment="prod"))

    def fake_run(app: str, host: str, port: int, reload: bool) -> None:
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    assert cli.main() is None
    assert captured == {
        "app": "procurement_spend_analysis.api.app:app",
        "host": "0.0.0.0",
        "port": 9123,
        "reload": False,
    }