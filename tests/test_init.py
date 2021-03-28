from currency_convertor import create_app


def test_config():
    """
    Test create_app without passing test config.
    """
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_db_url_environ(monkeypatch):
    """
    Test DATABASE_URL environment variable.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///environ")
    app = create_app()
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///environ"


def test_db_url_environ_absent(monkeypatch):
    """
    Test absence of DATABASE_URL environment variable.
    """
    try:
        monkeypatch.delenv("DATABASE_URL")
    except:
        pass
    app = create_app()
    assert "currency_convertor.sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]


def test_init_db_command(runner, monkeypatch):
    """
    Test the execution of the init-db command
    """

    class Recorder:
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("currency_convertor.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "Initialized" in result.output
    assert Recorder.called


def test_wsgi(appwsgi):
    assert "sqlite:///:memory:" in appwsgi.config["SQLALCHEMY_DATABASE_URI"]
