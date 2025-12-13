"""Test SpectrumProcessor class."""
import pytest
from cerespp.processor import SpectrumProcessor
from cerespp.logger import StructuredLogger


class TestSpectrumProcessor:
    """Test SpectrumProcessor class."""

    def test_creation(self):
        """Test creating a processor."""
        processor = SpectrumProcessor(mask='G2')
        assert processor.mask == 'G2'
        assert processor.logger is not None
        assert processor.progress_callback is None

    def test_creation_with_logger(self):
        """Test creating processor with custom logger."""
        logger = StructuredLogger('test')
        processor = SpectrumProcessor(mask='K0', logger=logger)
        assert processor.mask == 'K0'
        assert processor.logger == logger

    def test_creation_with_callback(self):
        """Test creating processor with progress callback."""
        called_steps = []

        def callback(step, **kwargs):
            called_steps.append(step)

        processor = SpectrumProcessor(progress_callback=callback)
        assert processor.progress_callback == callback

    def test_mask_options(self):
        """Test different mask options."""
        for mask in ['G2', 'K0', 'K5', 'M2']:
            processor = SpectrumProcessor(mask=mask)
            assert processor.mask == mask

    def test_timing_dict_initialization(self):
        """Test that timing dict is initialized."""
        processor = SpectrumProcessor()
        assert isinstance(processor.timing, dict)
        assert len(processor.timing) == 0


class TestSpectrumProcessorLogStep:
    """Test _log_step method."""

    def test_log_step_without_callback(self):
        """Test logging step without callback."""
        processor = SpectrumProcessor()
        # Should not raise
        processor._log_step("Test step", filename="test.fits")

    def test_log_step_with_callback(self):
        """Test logging step with callback."""
        called_steps = []
        called_kwargs = []

        def callback(step, **kwargs):
            called_steps.append(step)
            called_kwargs.append(kwargs)

        processor = SpectrumProcessor(progress_callback=callback)
        processor._log_step("Loading FITS", filename="test.fits")
        processor._log_step("Converting to rest frame", duration=5.2)

        assert len(called_steps) == 2
        assert called_steps[0] == "Loading FITS"
        assert called_steps[1] == "Converting to rest frame"
        assert called_kwargs[0] == {'filename': 'test.fits'}
        assert called_kwargs[1] == {'duration': 5.2}
