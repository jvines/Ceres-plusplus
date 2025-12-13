"""Test that all modules can be imported."""
import pytest


class TestImports:
    """Test module imports."""

    def test_import_cerespp(self):
        """Test importing main cerespp module."""
        import cerespp
        assert hasattr(cerespp, '__version__')

    def test_import_models(self):
        """Test importing models."""
        from cerespp.models import ProcessingResult, Spectrum1D
        assert ProcessingResult is not None
        assert Spectrum1D is not None

    def test_import_logger(self):
        """Test importing logger."""
        from cerespp.logger import StructuredLogger, default_logger
        assert StructuredLogger is not None
        assert default_logger is not None

    def test_import_processor(self):
        """Test importing processor."""
        from cerespp.processor import SpectrumProcessor
        assert SpectrumProcessor is not None

    def test_import_main_functions(self):
        """Test importing main functions."""
        from cerespp import get_activities, process_single_file
        assert get_activities is not None
        assert process_single_file is not None

    def test_import_legacy_functions(self):
        """Test importing legacy functions (backward compatibility)."""
        from cerespp import (
            ccf_gauss_plot, ccf_plot, line_plot,
            ccf, ccf_fit, median_combine, merge_echelle
        )
        assert ccf_gauss_plot is not None
        assert ccf_plot is not None
        assert line_plot is not None
        assert ccf is not None
        assert ccf_fit is not None
        assert median_combine is not None
        assert merge_echelle is not None

    def test_version_format(self):
        """Test that version is properly formatted."""
        import cerespp
        assert isinstance(cerespp.__version__, str)
        # Version should have at least one dot (e.g., "0.0.5")
        assert '.' in cerespp.__version__
