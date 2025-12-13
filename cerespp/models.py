"""Data models for Ceres++.

Defines structured result types for single-file and bulk processing.

Author: Jose Vines
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict
from datetime import datetime


@dataclass
class ProcessingResult:
    """Result of processing a single spectrum file.

    This dataclass provides a structured, JSON-serializable representation
    of all activity indicators and metadata from a single spectrum.

    Attributes
    ----------
    filename : str
        Path to the processed FITS file
    bjd : float
        Barycentric Julian Date
    rv : float
        Radial velocity from CCF (km/s)
    rv_error : float
        Error on radial velocity
    bis : float
        Bisector inverse slope
    bis_error : float
        Error on BIS
    fwhm : Optional[float]
        Full width at half maximum of CCF
    fwhm_error : Optional[float]
        Error on FWHM
    contrast : float
        CCF contrast (depth)
    s_index : float
        S-index (Ca H+K activity indicator)
    s_index_error : float
        Error on S-index
    halpha : float
        H-alpha activity indicator
    halpha_error : float
        Error on H-alpha
    hei : float
        HeI activity indicator
    hei_error : float
        Error on HeI
    nai_d1 : float
        NaI D1 component
    nai_d2 : float
        NaI D2 component
    nai_d1d2 : float
        Combined NaI D1+D2 activity indicator
    nai_d1d2_error : float
        Error on NaI D1+D2
    spectrum_1d_path : Optional[str]
        Path to saved 1D merged spectrum FITS file
    rest_frame_spectrum_path : Optional[str]
        Path to rest-frame corrected spectrum
    processing_time : Dict[str, float]
        Dictionary mapping step names to processing time in seconds
    errors : Optional[str]
        Error message if processing failed
    """

    filename: str
    bjd: float
    rv: float = 0.0
    rv_error: float = 0.0
    bis: float = 0.0
    bis_error: float = 0.0
    fwhm: Optional[float] = None
    fwhm_error: Optional[float] = None
    contrast: float = 0.0
    s_index: float = -999.0
    s_index_error: float = -999.0
    halpha: float = -999.0
    halpha_error: float = -999.0
    hei: float = -999.0
    hei_error: float = -999.0
    nai_d1: float = 0.0
    nai_d2: float = 0.0
    nai_d1d2: float = -999.0
    nai_d1d2_error: float = -999.0
    spectrum_1d_path: Optional[str] = None
    rest_frame_spectrum_path: Optional[str] = None
    processing_time: Dict[str, float] = field(default_factory=dict)
    errors: Optional[str] = None

    def to_dict(self):
        """Convert to JSON-serializable dictionary.

        Returns
        -------
        dict
            Dictionary representation of the result
        """
        return asdict(self)


@dataclass
class Spectrum1D:
    """Metadata for a 1D merged spectrum.

    This dataclass describes a single 1D merged spectrum file,
    including wavelength coverage, quality metrics, and file paths.

    Attributes
    ----------
    file_path : str
        Path to the 1D FITS file
    wavelengths_path : Optional[str]
        Path to NPY file with wavelength array
    fluxes_path : Optional[str]
        Path to NPY file with flux array
    errors_path : Optional[str]
        Path to NPY file with error array
    sn : float
        Signal-to-noise ratio
    wavelength_min : float
        Minimum wavelength in Angstroms
    wavelength_max : float
        Maximum wavelength in Angstroms
    num_points : int
        Number of wavelength points
    is_rest_frame : bool
        True if spectrum is in rest frame
    created_at : datetime
        Timestamp of creation
    instrument : Optional[str]
        Instrument name (e.g., FEROS, HARPS)
    """

    file_path: str
    sn: float
    wavelength_min: float
    wavelength_max: float
    num_points: int
    wavelengths_path: Optional[str] = None
    fluxes_path: Optional[str] = None
    errors_path: Optional[str] = None
    is_rest_frame: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    instrument: Optional[str] = None

    def to_dict(self):
        """Convert to JSON-serializable dictionary.

        Returns
        -------
        dict
            Dictionary representation with datetime converted to ISO format
        """
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result
