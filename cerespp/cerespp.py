"""cerespp.

Main routine for ceres plusplus.

Author: Jose Vines
"""
import numpy as np
from astropy.io import fits
from tqdm import tqdm
from typing import Optional, Callable

from .constants import *
from .spectra_utils import correct_to_rest
from .spectra_utils import merge_echelle
from .utils import create_dir
from .utils import get_line_flux
from .processor import SpectrumProcessor
from .models import ProcessingResult
from .logger import StructuredLogger


def get_activities(files, out, mask='G2', save=False,
                   logger: Optional[StructuredLogger] = None,
                   progress_callback: Optional[Callable] = None):
    """Main function (backward compatible).

    This function now delegates to SpectrumProcessor for each file,
    providing granular logging and progress tracking while maintaining
    the same output format for backward compatibility.

    Parameters
    ----------
    files: array_like
        An array or list with the spectra filenames.
    out: str
        The output directory for the results.
    mask: str, optional
        The selected mask for calculating the RV. Options are G2, K0, K5 and M2
    save: bool, optional
        Save the individual merged spectra? Default is False.
    logger : Optional[StructuredLogger]
        Logger instance for structured logging
    progress_callback : Optional[Callable]
        Callback function for progress updates

    Returns
    -------
    data: array_like
        An array with the activity indices.
    header: array_like
        An array with the activity indices identifiers.

    """
    create_dir(out)
    processor = SpectrumProcessor(mask=mask, logger=logger,
                                 progress_callback=progress_callback)

    results = []
    for fname in tqdm(files, desc="Processing spectra"):
        try:
            result = processor.process_file(fname, out, save_1d=save)
            results.append(result)
        except Exception as e:
            if logger:
                logger.error(f"Failed to process {fname}: {e}")
            # Continue with next file instead of crashing
            results.append(ProcessingResult(filename=fname, errors=str(e)))

    # Convert to legacy output format for backward compatibility
    return _convert_to_legacy_format(results, out)


def process_single_file(filename: str, out: str, mask: str = 'G2',
                       save: bool = True,
                       logger: Optional[StructuredLogger] = None,
                       progress_callback: Optional[Callable] = None) -> ProcessingResult:
    """Process a single file (new microservice-friendly interface).

    This function provides a clean API for processing individual files,
    returning structured results instead of bulk arrays.

    Parameters
    ----------
    filename : str
        Path to FITS file to process
    out : str
        Output directory for results
    mask : str, optional
        Mask for RV calculation ('G2', 'K0', 'K5', 'M2'). Default is 'G2'.
    save : bool, optional
        Save merged 1D spectrum to FITS file. Default is True.
    logger : Optional[StructuredLogger]
        Logger instance for structured logging
    progress_callback : Optional[Callable]
        Callback function called after each processing step

    Returns
    -------
    ProcessingResult
        Structured result with all activity indicators

    Examples
    --------
    >>> result = process_single_file('spectrum.fits', 'output/', mask='G2')
    >>> print(f"S-index: {result.s_index:.3f}")
    S-index: 0.234

    >>> def callback(step, **kwargs):
    ...     print(f"Processing: {step}")
    >>> result = process_single_file('spectrum.fits', 'output/',
    ...                              progress_callback=callback)
    Processing: Loading FITS file
    Processing: Converting to rest frame
    ...
    """
    create_dir(out)
    processor = SpectrumProcessor(mask=mask, logger=logger,
                                 progress_callback=progress_callback)
    return processor.process_file(filename, out, save_1d=save)


def _convert_to_legacy_format(results, out):
    """Convert list of ProcessingResult to legacy output format.

    Parameters
    ----------
    results : list of ProcessingResult
        Structured results from processing
    out : str
        Output directory

    Returns
    -------
    data : numpy.ndarray
        Array with activity indices (legacy format)
    header : str
        Header string with column names (legacy format)
    """
    # Extract arrays from results
    bjd = []
    s_indices = []
    s_err = []
    ha = []
    ha_err = []
    hei = []
    hei_err = []
    nai = []
    nai_err = []
    bis = []
    bis_err = []
    fwhm = []
    fwhm_err = []
    contrast = []

    has_fwhm = False
    targ_name = "unknown"

    for result in results:
        if result.errors:
            # Skip failed files
            continue

        bjd.append(result.bjd)
        s_indices.append(result.s_index)
        s_err.append(result.s_index_error)
        ha.append(result.halpha)
        ha_err.append(result.halpha_error)
        hei.append(result.hei)
        hei_err.append(result.hei_error)
        nai.append(result.nai_d1d2)
        nai_err.append(result.nai_d1d2_error)
        bis.append(result.bis)
        bis_err.append(result.bis_error)
        contrast.append(result.contrast)

        if result.fwhm is not None:
            has_fwhm = True
            fwhm.append(result.fwhm)
            fwhm_err.append(result.fwhm_error)

        # Get target name from first file
        if targ_name == "unknown" and result.filename:
            try:
                hdul = fits.open(result.filename)
                targ_name = hdul[0].header.get('HIERARCH TARGET NAME', 'unknown')
                hdul.close()
            except:
                pass

    # Build output arrays
    if has_fwhm:
        header = 'bjd S e_S Halpha e_Halpha HeI'
        header += ' e_HeI NaID1D2 e_NaID1D2 BIS e_BIS FWHM e_FWHM CONTRAST'

        data = np.vstack([
            bjd,
            s_indices, s_err,
            ha, ha_err,
            hei, hei_err,
            nai, nai_err,
            bis, bis_err,
            fwhm, fwhm_err,
            contrast
        ]).T
    else:
        header = 'bjd S e_S Halpha e_Halpha HeI'
        header += ' e_HeI NaID1D2 e_NaID1D2 BIS e_BIS CONTRAST'

        data = np.vstack([
            bjd,
            s_indices, s_err,
            ha, ha_err,
            hei, hei_err,
            nai, nai_err,
            bis, bis_err,
            contrast
        ]).T

    # Save to file (maintaining backward compatibility)
    np.savetxt(f'{out}/{targ_name}_activities.dat', data, header=header)

    return data, header