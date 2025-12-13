"""Test data models."""
import pytest
from datetime import datetime
from cerespp.models import ProcessingResult, Spectrum1D


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_creation(self):
        """Test creating a ProcessingResult."""
        result = ProcessingResult(
            filename="test.fits",
            bjd=2459000.5,
            s_index=0.234,
            s_index_error=0.002,
            halpha=0.456,
            halpha_error=0.003,
            hei=0.789,
            hei_error=0.004,
            nai_d1d2=0.123,
            nai_d1d2_error=0.001,
            bis=0.05,
            bis_error=0.001,
            contrast=0.8,
        )

        assert result.filename == "test.fits"
        assert result.bjd == 2459000.5
        assert result.s_index == 0.234
        assert result.errors is None

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ProcessingResult(
            filename="test.fits",
            bjd=2459000.5,
            s_index=0.234,
            s_index_error=0.002,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['filename'] == "test.fits"
        assert result_dict['bjd'] == 2459000.5
        assert result_dict['s_index'] == 0.234

    def test_with_errors(self):
        """Test ProcessingResult with error message."""
        result = ProcessingResult(
            filename="test.fits",
            bjd=0.0,
            errors="File not found"
        )

        assert result.errors == "File not found"
        assert result.bjd == 0.0

    def test_processing_time(self):
        """Test processing_time dict."""
        result = ProcessingResult(
            filename="test.fits",
            bjd=2459000.5,
            processing_time={
                'load_fits': 0.5,
                'rest_frame': 5.2,
                'merge_echelle': 120.3,
                's_index': 1.0,
                'halpha': 0.8,
                'hei': 0.7,
                'nai': 0.6
            }
        )

        assert result.processing_time['rest_frame'] == 5.2
        assert result.processing_time['merge_echelle'] == 120.3
        assert len(result.processing_time) == 7


class TestSpectrum1D:
    """Test Spectrum1D dataclass."""

    def test_creation(self):
        """Test creating a Spectrum1D."""
        spectrum = Spectrum1D(
            file_path="/path/to/spectrum.fits",
            sn=100.5,
            wavelength_min=3800.0,
            wavelength_max=6900.0,
            num_points=50000,
            is_rest_frame=True,
            instrument="FEROS"
        )

        assert spectrum.file_path == "/path/to/spectrum.fits"
        assert spectrum.sn == 100.5
        assert spectrum.wavelength_min == 3800.0
        assert spectrum.wavelength_max == 6900.0
        assert spectrum.is_rest_frame is True
        assert spectrum.instrument == "FEROS"

    def test_to_dict(self):
        """Test converting to dictionary."""
        spectrum = Spectrum1D(
            file_path="/path/to/spectrum.fits",
            sn=100.5,
            wavelength_min=3800.0,
            wavelength_max=6900.0,
            num_points=50000
        )

        spectrum_dict = spectrum.to_dict()

        assert isinstance(spectrum_dict, dict)
        assert spectrum_dict['file_path'] == "/path/to/spectrum.fits"
        assert spectrum_dict['sn'] == 100.5
        assert 'created_at' in spectrum_dict
        # created_at should be ISO format string
        assert isinstance(spectrum_dict['created_at'], str)

    def test_default_values(self):
        """Test default values."""
        spectrum = Spectrum1D(
            file_path="/path/to/spectrum.fits",
            sn=100.5,
            wavelength_min=3800.0,
            wavelength_max=6900.0,
            num_points=50000
        )

        assert spectrum.wavelengths_path is None
        assert spectrum.fluxes_path is None
        assert spectrum.errors_path is None
        assert spectrum.is_rest_frame is False
        assert spectrum.instrument is None
        assert isinstance(spectrum.created_at, datetime)
