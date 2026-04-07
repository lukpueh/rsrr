from typing import Any
from unittest.mock import patch
import json

from click.testing import CliRunner

from rsrr.base import BaseCheck, Context
from rsrr.cli import main


# -- Fake checks --


class FakeCheckA(BaseCheck):
    name = "Check A"
    comment = "First fake check"

    async def run(self) -> Any:
        return "result_a"


class FakeCheckB(BaseCheck):
    name = "Check B"
    comment = "Second fake check"

    async def run(self) -> Any:
        return "result_b"


FAKE_CHECKS = {"check_a": FakeCheckA, "check_b": FakeCheckB}


def _patch_checks(checks=None):
    if checks is None:
        checks = FAKE_CHECKS
    return patch("rsrr.cli.get_all_checks", return_value=checks)


# -- Tests --


def test_main_no_subcommand_shows_help():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "Rapid Security Review Runner" in result.output


def test_list_shows_checks():
    with _patch_checks():
        runner = CliRunner()
        result = runner.invoke(main, ["list"])
    assert result.exit_code == 0
    assert "check_a" in result.output
    assert "Check A" in result.output
    assert "check_b" in result.output


def test_run_all_checks():
    with _patch_checks():
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--ef-project-id", "test.project"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["check_a"] == "result_a"
    assert data["check_b"] == "result_b"


def test_run_specific_check():
    with _patch_checks():
        runner = CliRunner()
        result = runner.invoke(
            main, ["run", "--ef-project-id", "test.project", "check_a"]
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["check_a"] == "result_a"
    assert "check_b" not in data


def test_run_unknown_check():
    with _patch_checks():
        runner = CliRunner()
        result = runner.invoke(
            main, ["run", "--ef-project-id", "test.project", "nonexistent"]
        )

    assert result.exit_code == 1
    assert "Unknown checks" in result.output
    assert "nonexistent" in result.output


def test_run_with_ctx_data(tmp_path):
    ctx_file = tmp_path / "ctx.json"
    ctx_file.write_text('{"check_a": "cached"}')

    with _patch_checks():
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["run", "--ef-project-id", "test.project", "--ctx-data", str(ctx_file)],
        )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["check_a"] == "cached"
    assert data["check_b"] == "result_b"


def test_run_with_invalid_ctx_data(tmp_path):
    ctx_file = tmp_path / "bad.json"
    ctx_file.write_text("not-json")

    runner = CliRunner()
    result = runner.invoke(
        main, ["run", "--ef-project-id", "test.project", "--ctx-data", str(ctx_file)]
    )
    assert result.exit_code == 1
    assert "Invalid JSON" in result.output


def test_run_with_non_object_ctx_data(tmp_path):
    ctx_file = tmp_path / "array.json"
    ctx_file.write_text("[1, 2]")

    runner = CliRunner()
    result = runner.invoke(
        main, ["run", "--ef-project-id", "test.project", "--ctx-data", str(ctx_file)]
    )
    assert result.exit_code == 1
    assert "--ctx-data file must contain a JSON object" in result.output


def test_run_with_gh_token():
    """--gh-token is passed through to Context."""
    with _patch_checks(), patch("rsrr.cli.Context") as mock_ctx_cls:
        mock_ctx_cls.return_value = Context(gh_token="tok123")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["run", "--ef-project-id", "test.project", "--gh-token", "tok123"],
        )

    assert result.exit_code == 0
    mock_ctx_cls.assert_called_once_with(
        ef_project_id="test.project", gh_token="tok123", data={}
    )


def test_run_gh_token_from_env():
    """GH_TOKEN env var is used when --gh-token is not provided."""
    with _patch_checks(), patch("rsrr.cli.Context") as mock_ctx_cls:
        mock_ctx_cls.return_value = Context(gh_token="env-token")
        runner = CliRunner(env={"GH_TOKEN": "env-token"})
        result = runner.invoke(
            main,
            ["run", "--ef-project-id", "test.project"],
        )

    assert result.exit_code == 0
    mock_ctx_cls.assert_called_once_with(
        ef_project_id="test.project", gh_token="env-token", data={}
    )


def test_run_no_checks_available():
    with _patch_checks(checks={}):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--ef-project-id", "test.project"])

    assert result.exit_code == 1
    assert "No checks to run" in result.output
