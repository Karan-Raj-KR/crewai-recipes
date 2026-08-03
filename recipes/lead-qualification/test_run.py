import pytest
import sys
from unittest.mock import patch, MagicMock
from run import main, parse_args

def test_missing_args(capsys):
    # Missing args should trigger argparse error and exit 2
    with patch.object(sys, "argv", ["run.py"]):
        with pytest.raises(SystemExit) as exc:
            parse_args()
        assert exc.value.code == 2

def test_whitespace_args(capsys):
    # Whitespace only args should exit 1
    with patch.object(sys, "argv", ["run.py", "--company", "   ", "--description", "   "]):
        # Mock preflight and build_crew to isolate run logic
        with patch("run.preflight"), patch("crew.build_crew"):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
            captured = capsys.readouterr()
            assert "Error: --company and --description cannot be empty" in captured.out

def test_run_success():
    with patch.object(sys, "argv", ["run.py", "--company", "Acme", "--description", "Test"]):
        with patch("run.preflight"):
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = "Success output"
            with patch("crew.build_crew", return_value=mock_crew) as mock_build:
                main()
                mock_build.assert_called_once_with(company="Acme", description="Test")
                mock_crew.kickoff.assert_called_once()
