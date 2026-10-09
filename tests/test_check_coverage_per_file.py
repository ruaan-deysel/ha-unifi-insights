# Copyright 2026 UniFi Insights contributors
"""Tests for script/check_coverage_per_file.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "script" / "check_coverage_per_file.py"
)


@pytest.fixture(scope="module")
def check_coverage_module() -> Any:
    """Load the check_coverage_per_file script as a module."""
    spec = importlib.util.spec_from_file_location(
        "check_coverage_per_file", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _create_coverage_xml(
    tmp_path: Path,
    filename: str,
    classes_xml: str,
) -> Path:
    xml_content = f"""<?xml version="1.0" ?>
<coverage version="7.0">
  <packages>
    <package name="pkg">
      <classes>
        {classes_xml}
      </classes>
    </package>
  </packages>
</coverage>
"""
    xml_file = tmp_path / filename
    xml_file.write_text(xml_content, encoding="utf-8")
    return xml_file


def test_all_pass(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that exit 0 is returned when all files meet the threshold."""
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_pass.xml",
        """
        <class name="mod1.py" filename="custom_components/mod1.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
        """,
    )
    code = check_coverage_module.main([str(xml_path)])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "meet or exceed 95% coverage threshold" in out


def test_one_file_below(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that exit 1 is returned and the failing file is named in the output."""
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_fail.xml",
        """
        <class name="passing.py" filename="custom_components/passing.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
        <class name="failing.py" filename="custom_components/failing.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
          </lines>
        </class>
        """,
    )
    code = check_coverage_module.main([str(xml_path)])
    out, _ = capsys.readouterr()
    assert code == 1
    assert "custom_components/failing.py" in out
    assert "50.00%" in out
    assert "1 file(s) below 95% coverage threshold" in out
    # Ensure passing file is not listed in failing section
    lines = out.strip().splitlines()
    assert not any("passing.py" in line for line in lines[:-1])


def test_partial_line_counts_as_not_covered(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a partial branch line counts as not covered."""
    # Line 1: hits=1, branch="true", condition-coverage="50% (1/2)" -> partial
    # Line 2: hits=1 -> hit
    # Total = 2, hits = 1, partial = 1, missed = 0 -> pct = 50.0%
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_partial.xml",
        """
        <class name="partial_file.py" filename="custom_components/partial_file.py">
          <lines>
            <line number="1" hits="1" branch="true" condition-coverage="50% (1/2)"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
        """,
    )
    code = check_coverage_module.main([str(xml_path), "--fail-under", "95"])
    out, _ = capsys.readouterr()
    assert code == 1
    assert "custom_components/partial_file.py" in out
    assert "partial=1" in out
    assert "50.00%" in out


def test_zero_measurable_lines_passes(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a file with 0 measurable lines passes."""
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_empty.xml",
        """
        <class name="empty.py" filename="custom_components/empty.py">
          <lines>
          </lines>
        </class>
        """,
    )
    code = check_coverage_module.main([str(xml_path)])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "meet or exceed 95% coverage threshold" in out


def test_fail_under_option_honoured(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that --fail-under flag is respected."""
    # 9 hits out of 10 lines = 90.0%
    lines_xml = "".join(f'<line number="{i}" hits="1"/>' for i in range(1, 10))
    lines_xml += '<line number="10" hits="0"/>'
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_ninety.xml",
        f"""
        <class name="ninety.py" filename="custom_components/ninety.py">
          <lines>
            {lines_xml}
          </lines>
        </class>
        """,
    )
    # With 95% threshold: fails
    code_95 = check_coverage_module.main([str(xml_path), "--fail-under", "95"])
    out_95, _ = capsys.readouterr()
    assert code_95 == 1
    assert "custom_components/ninety.py" in out_95

    # With 90% threshold: passes (90.0% >= 90.0%)
    code_90 = check_coverage_module.main([str(xml_path), "--fail-under", "90"])
    out_90, _ = capsys.readouterr()
    assert code_90 == 0
    assert "meet or exceed 90% coverage threshold" in out_90

    # With 80% threshold: passes
    code_80 = check_coverage_module.main([str(xml_path), "--fail-under", "80"])
    out_80, _ = capsys.readouterr()
    assert code_80 == 0
    assert "meet or exceed 80% coverage threshold" in out_80


def test_missing_file_error_and_exit_2(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that a missing file produces a clear error and exits with code 2."""
    missing_path = tmp_path / "nonexistent.xml"
    code = check_coverage_module.main([str(missing_path)])
    _, err = capsys.readouterr()
    assert code == 2
    assert f"Error: coverage file '{missing_path}' not found." in err


def test_malformed_xml_error_and_exit_2(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that malformed XML produces an error and exits with code 2."""
    bad_xml = tmp_path / "bad.xml"
    bad_xml.write_text("<invalid>xml", encoding="utf-8")
    code = check_coverage_module.main([str(bad_xml)])
    _, err = capsys.readouterr()
    assert code == 2
    assert "Error: failed to parse" in err


def test_fully_covered_branch_line_counts_as_hit(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A branch line with all conditions covered is a hit, not a partial."""
    xml_path = _create_coverage_xml(
        tmp_path,
        "cov_full_branch.xml",
        """
        <class name="branch.py" filename="custom_components/branch.py">
          <lines>
            <line number="1" hits="1" branch="true" condition-coverage="100% (2/2)"/>
          </lines>
        </class>
        """,
    )
    code, failing, rows = check_coverage_module.check_coverage(xml_path)
    assert code == 0
    assert failing == []
    assert rows[0]["hits"] == 1
    assert rows[0]["partial"] == []
    assert rows[0]["pct"] == 100.0
    assert check_coverage_module.main([str(xml_path)]) == 0
    out, err = capsys.readouterr()
    assert "All 1 file(s) meet or exceed 95% coverage threshold" in out
    assert err == ""


def test_no_file_rows_error_and_exit_2(
    check_coverage_module: Any, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An XML report without classes is invalid coverage input."""
    xml_path = _create_coverage_xml(tmp_path, "cov_no_files.xml", "")
    assert check_coverage_module.check_coverage(xml_path) == (2, [], [])
    assert check_coverage_module.main([str(xml_path)]) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert f"Error: no file rows found in '{xml_path}'." in err
