"""Test CLI interface."""
import pytest
import subprocess
import sys


class TestCLI:
    """Test command-line interface."""

    def test_help_command(self):
        """Test --help flag."""
        result = subprocess.run(
            [sys.executable, '-m', 'cerespp', '--help'],
            capture_output=True,
            text=True,
            cwd='.'
        )

        assert result.returncode == 0
        assert 'Ceres++ Activity Analysis' in result.stdout
        assert '--file' in result.stdout
        assert '--files' in result.stdout
        assert '--output' in result.stdout
        assert '--mask' in result.stdout

    def test_no_arguments(self):
        """Test running without arguments (should fail)."""
        result = subprocess.run(
            [sys.executable, '-m', 'cerespp'],
            capture_output=True,
            text=True,
            cwd='.'
        )

        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or 'error' in result.stderr.lower()

    def test_missing_output(self):
        """Test running without --output (should fail)."""
        result = subprocess.run(
            [sys.executable, '-m', 'cerespp', '--file', 'test.fits'],
            capture_output=True,
            text=True,
            cwd='.'
        )

        assert result.returncode != 0
        assert 'required' in result.stderr.lower() or '--output' in result.stderr.lower()

    def test_mask_choices(self):
        """Test that only valid mask choices are accepted."""
        result = subprocess.run(
            [sys.executable, '-m', 'cerespp', '--file', 'test.fits',
             '--output', 'out/', '--mask', 'INVALID'],
            capture_output=True,
            text=True,
            cwd='.'
        )

        assert result.returncode != 0
        # Should mention valid choices
        assert 'G2' in result.stderr or 'invalid choice' in result.stderr.lower()

    def test_mutually_exclusive_file_options(self):
        """Test that --file and --files are mutually exclusive."""
        result = subprocess.run(
            [sys.executable, '-m', 'cerespp',
             '--file', 'test1.fits',
             '--files', 'test2.fits', 'test3.fits',
             '--output', 'out/'],
            capture_output=True,
            text=True,
            cwd='.'
        )

        assert result.returncode != 0
        assert 'mutually exclusive' in result.stderr.lower() or 'not allowed' in result.stderr.lower()
