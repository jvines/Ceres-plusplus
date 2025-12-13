"""
Ceres plusplus is a module designed to extend the functionality of ceres
(https://github.com/rabrahm/ceres) in order to calculate activity indicators
from spectra reduced with the tool, and to easily extract the indicators that
ceres does calculate, for example the CCF FWHM and the BIS.
"""
try:
    from importlib.metadata import version
    __version__ = version('cerespp')
except Exception:
    __version__ = '1.3.0'

from .cerespp import get_activities, process_single_file
from .cpplots import ccf_gauss_plot
from .cpplots import ccf_plot
from .cpplots import line_plot
from .cpplots import line_plot_from_file
from .crosscorr import ccf
from .crosscorr import ccf_fit
from .spectra_utils import median_combine
from .spectra_utils import median_combine_1d
from .spectra_utils import merge_echelle
from .spectra_utils import velocity_correction
from .spectra_utils import correct_to_rest
from .models import ProcessingResult, Spectrum1D
from .processor import SpectrumProcessor
from .logger import StructuredLogger
