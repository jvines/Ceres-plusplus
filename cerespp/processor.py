"""Single-file spectrum processor for Ceres++.

Provides granular per-step processing with progress tracking and logging.

Author: Jose Vines
"""
import time
import os
import logging
import numpy as np
from astropy.io import fits
from typing import Optional, Callable

from .models import ProcessingResult
from .constants import *
from .spectra_utils import correct_to_rest, merge_echelle
from .utils import get_line_flux


class SpectrumProcessor:
    """Process a single spectrum file with granular logging.

    This class extracts the per-file processing logic from the bulk
    get_activities() function, enabling:
    - Granular step-by-step logging
    - Progress callbacks for external monitoring
    - Structured result output
    - Better error handling

    Parameters
    ----------
    mask : str
        Mask for RV calculation ('G2', 'K0', 'K5', or 'M2')
    logger : Optional[logging.Logger]
        Logger instance. If None, uses default logger.
    progress_callback : Optional[Callable]
        Function called after each processing step.
        Signature: callback(step_name: str, **kwargs)

    Attributes
    ----------
    mask : str
        Selected mask
    logger : logging.Logger
        Logger instance
    progress_callback : Optional[Callable]
        Progress callback function
    timing : dict
        Dictionary tracking time spent in each step

    Examples
    --------
    >>> processor = SpectrumProcessor(mask='G2')
    >>> result = processor.process_file('spectrum.fits', 'output/')
    >>> print(f"S-index: {result.s_index:.3f}")

    With progress callback:
    >>> def callback(step, **kwargs):
    ...     print(f"Step: {step}")
    >>> processor = SpectrumProcessor(progress_callback=callback)
    >>> result = processor.process_file('spectrum.fits', 'output/')
    """

    def __init__(self, mask: str = 'G2',
                 logger: Optional[logging.Logger] = None,
                 progress_callback: Optional[Callable] = None):
        """Initialize spectrum processor.

        Parameters
        ----------
        mask : str
            Mask for RV calculation
        logger : Optional[logging.Logger]
            Logger instance
        progress_callback : Optional[Callable]
            Progress callback function
        """
        self.mask = mask
        self.logger = logger or logging.getLogger('cerespp')
        self.progress_callback = progress_callback
        self.timing = {}

    def process_file(self, filename: str, output_dir: str,
                     save_1d: bool = True) -> ProcessingResult:
        """Process a single FITS file through all steps.

        Parameters
        ----------
        filename : str
            Path to FITS file
        output_dir : str
            Output directory for results
        save_1d : bool
            Save merged 1D spectrum to FITS file

        Returns
        -------
        ProcessingResult
            Structured result with all activity indicators

        Raises
        ------
        Exception
            If any processing step fails, returns ProcessingResult with error
        """
        start_time = time.time()

        try:
            # Step 1: Load FITS file
            self._log_step("Loading FITS file", filename=filename)
            step_start = time.time()
            hdul, data, header_data = self._load_fits(filename)
            self.timing['load_fits'] = time.time() - step_start

            # Step 2: Rest frame conversion
            self._log_step("Converting to rest frame")
            step_start = time.time()
            w, f = self._rest_frame_conversion(data)
            self.timing['rest_frame'] = time.time() - step_start

            # Step 3: Merge echelle orders
            self._log_step("Merging echelle orders")
            step_start = time.time()
            waves, fluxes, errors, sn = self._merge_orders(
                data, w, f, hdul[0].header, output_dir, save_1d
            )
            self.timing['merge_echelle'] = time.time() - step_start

            spectrum_1d_path = None
            if save_1d:
                # Construct path where merge_echelle saves the file
                targ_name = hdul[0].header.get('HIERARCH TARGET NAME', 'unknown')
                bjd = hdul[0].header.get('BJD_OUT', 0.0)
                spectrum_1d_path = f"{output_dir}/{targ_name}_{bjd}.fits"

            hdul.close()

            # Determine instrument for S-index exception handling
            inst = header_data.get('instrument', '').lower()

            # Step 4: Calculate S-index
            self._log_step("Calculating S-index")
            step_start = time.time()
            s_index, s_index_error = self._calculate_s_index(
                waves, fluxes, errors, inst
            )
            self.timing['s_index'] = time.time() - step_start

            # Step 5: Calculate H-alpha
            self._log_step("Calculating H-alpha")
            step_start = time.time()
            halpha, halpha_error = self._calculate_halpha(waves, fluxes, errors)
            self.timing['halpha'] = time.time() - step_start

            # Step 6: Calculate HeI
            self._log_step("Calculating HeI")
            step_start = time.time()
            hei, hei_error = self._calculate_hei(waves, fluxes, errors)
            self.timing['hei'] = time.time() - step_start

            # Step 7: Calculate NaI D1/D2
            self._log_step("Calculating NaI D1/D2")
            step_start = time.time()
            nai_d1d2, nai_d1d2_error = self._calculate_nai(waves, fluxes, errors)
            self.timing['nai'] = time.time() - step_start

            total_time = time.time() - start_time
            self._log_step("Processing completed", duration=total_time)

            # Build result
            result = ProcessingResult(
                filename=filename,
                bjd=header_data['bjd'],
                rv=0.0,  # Not directly available from current code
                rv_error=0.0,
                bis=header_data['bis'],
                bis_error=header_data['bis_error'],
                fwhm=header_data.get('fwhm'),
                fwhm_error=header_data.get('fwhm_error'),
                contrast=header_data['contrast'],
                s_index=s_index,
                s_index_error=s_index_error,
                halpha=halpha,
                halpha_error=halpha_error,
                hei=hei,
                hei_error=hei_error,
                nai_d1d2=nai_d1d2,
                nai_d1d2_error=nai_d1d2_error,
                spectrum_1d_path=spectrum_1d_path,
                processing_time=self.timing.copy()
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to process {filename}: {str(e)}")
            return ProcessingResult(
                filename=filename,
                bjd=0.0,
                errors=str(e)
            )

    def _extract_bisector_with_fallback(self, filename: str, header):
        """Extract bisector with fallback: BS from header → BS2 from results.txt → -999

        Parameters
        ----------
        filename : str
            Path to FITS file
        header : astropy.io.fits.Header
            FITS header object

        Returns
        -------
        bis : float
            Bisector span value
        bis_error : float
            Bisector span error
        """
        # Step 1: Try BS from FITS header first
        bis = header.get('BS', -999.0)
        bis_error = header.get('BS_E', -999.0)

        if bis != -999.0:
            return bis, bis_error

        # Step 2: BS missing, try BS2 from results.txt
        try:
            from pathlib import Path
            results_file = Path(filename).parent.parent / 'proc' / 'results.txt'

            if results_file.exists():
                with open(results_file, 'r') as f:
                    # Parse each line looking for matching filename
                    fits_name = Path(filename).name
                    for line in f:
                        if fits_name in line or Path(filename).stem in line:
                            parts = line.split()
                            if len(parts) >= 6:
                                bis2 = float(parts[4])  # Column 5 (0-indexed column 4)
                                if bis2 != -999.0:
                                    return bis2, float(parts[5])  # BS2 and error
        except Exception:
            # Silent failure - fallback to -999
            pass

        # Step 3: Both missing, return -999
        return -999.0, -999.0

    def _load_fits(self, filename: str):
        """Load FITS file and extract header data.

        Parameters
        ----------
        filename : str
            Path to FITS file

        Returns
        -------
        hdul : astropy.io.fits.HDUList
            FITS HDU list
        data : numpy.ndarray
            FITS data array
        header_data : dict
            Dictionary with extracted header values
        """
        hdul = fits.open(filename)
        data = hdul[0].data
        header = hdul[0].header

        # Extract bisector with fallback logic
        bis, bis_error = self._extract_bisector_with_fallback(filename, header)

        header_data = {
            'bjd': header.get('BJD_OUT', 0.0),
            'bis': bis,
            'bis_error': bis_error,
            'contrast': header.get('XC_MIN', 0.0),
            'instrument': header.get('INST', 'unknown')
        }

        # FWHM is optional
        try:
            header_data['fwhm'] = header['FWHM']
            header_data['fwhm_error'] = header['DISP'] / header['SNR']
        except KeyError:
            header_data['fwhm'] = None
            header_data['fwhm_error'] = None

        return hdul, data, header_data

    def _rest_frame_conversion(self, data: np.ndarray):
        """Convert spectrum to rest frame.

        Parameters
        ----------
        data : numpy.ndarray
            FITS data array

        Returns
        -------
        w : numpy.ndarray
            Rest-frame wavelengths
        f : numpy.ndarray
            Rest-frame fluxes
        """
        w, f = correct_to_rest(data, mask=self.mask)
        return w, f

    def _merge_orders(self, data: np.ndarray, w: np.ndarray, f: np.ndarray,
                      header, output_dir: str, save: bool):
        """Merge echelle orders into 1D spectrum.

        Parameters
        ----------
        data : numpy.ndarray
            FITS data array
        w : numpy.ndarray
            Rest-frame wavelengths
        f : numpy.ndarray
            Rest-frame fluxes
        header : astropy.io.fits.Header
            FITS header
        output_dir : str
            Output directory
        save : bool
            Save merged spectrum to file

        Returns
        -------
        waves : numpy.ndarray
            Merged wavelength array
        fluxes : numpy.ndarray
            Merged flux array
        errors : numpy.ndarray
            Merged error array
        sn : float
            Signal-to-noise ratio
        """
        prod = np.stack((w, f, data[2, :, :], data[8, :, :]))
        waves, fluxes, errors, sn = merge_echelle(
            prod, header, out=output_dir, save=save
        )
        return waves, fluxes, errors, sn

    def _calculate_s_index(self, waves: np.ndarray, fluxes: np.ndarray,
                           errors: np.ndarray, inst: str):
        """Calculate S-index (Ca H+K activity).

        Parameters
        ----------
        waves : numpy.ndarray
            Wavelength array
        fluxes : numpy.ndarray
            Flux array
        errors : numpy.ndarray
            Error array
        inst : str
            Instrument name (lowercase)

        Returns
        -------
        s_index : float
            S-index value
        s_index_error : float
            Error on S-index
        """
        # FIDEOS doesn't reach Ca HK
        if inst in s_exceptions:
            return -999.0, -999.0

        # CaV (continuum violet)
        NV, sNV = get_line_flux(waves, fluxes, CaV, 20,
                                filt='square', error=errors)

        # CaR (continuum red)
        NR, sNR = get_line_flux(waves, fluxes, CaR, 20,
                                filt='square', error=errors)

        # CaK line
        NK, sNK = get_line_flux(waves, fluxes, CaK, 1.09,
                                filt='triangle', error=errors)

        # CaH line
        NH, sNH = get_line_flux(waves, fluxes, CaH, 1.09,
                                filt='triangle', error=errors)

        S = (NH + NK) / (NR + NV)
        sSnum = np.sqrt(sNH ** 2 + sNK ** 2)
        sSden = np.sqrt(sNV ** 2 + sNR ** 2)
        sS = S * np.sqrt((sSnum / (NH + NK)) ** 2 + (sSden / (NR + NV)) ** 2)

        return S, sS

    def _calculate_halpha(self, waves: np.ndarray, fluxes: np.ndarray,
                          errors: np.ndarray):
        """Calculate H-alpha activity indicator.

        Parameters
        ----------
        waves : numpy.ndarray
            Wavelength array
        fluxes : numpy.ndarray
            Flux array
        errors : numpy.ndarray
            Error array

        Returns
        -------
        halpha : float
            H-alpha value
        halpha_error : float
            Error on H-alpha
        """
        # H-alpha line
        FHa, sFHa = get_line_flux(waves, fluxes, Ha, 0.678,
                                  filt='square', error=errors)

        # Continuum F1
        F1, sF1 = get_line_flux(waves, fluxes, 6550.87, 10.75,
                                filt='square', error=errors)

        # Continuum F2
        F2, sF2 = get_line_flux(waves, fluxes, 6580.309, 8.75,
                                filt='square', error=errors)

        Halpha = FHa / (0.5 * (F1 + F2))
        sden = np.sqrt(sF1 ** 2 + sF2 ** 2)
        sHalpha = Halpha * np.sqrt((sFHa / FHa) ** 2 + (sden / (F1 + F2)) ** 2)

        return Halpha, sHalpha

    def _calculate_hei(self, waves: np.ndarray, fluxes: np.ndarray,
                       errors: np.ndarray):
        """Calculate HeI activity indicator.

        Parameters
        ----------
        waves : numpy.ndarray
            Wavelength array
        fluxes : numpy.ndarray
            Flux array
        errors : numpy.ndarray
            Error array

        Returns
        -------
        hei : float
            HeI value
        hei_error : float
            Error on HeI
        """
        # HeI line
        FHeI, sFHeI = get_line_flux(waves, fluxes, HeI, 0.2,
                                    filt='square', error=errors)

        # Continuum F1
        F1, sF1 = get_line_flux(waves, fluxes, 5874.5, 0.5,
                                filt='square', error=errors)

        # Continuum F2
        F2, sF2 = get_line_flux(waves, fluxes, 5879, 0.5,
                                filt='square', error=errors)

        HelI = FHeI / (0.5 * (F1 + F2))
        sden = np.sqrt(sF1 ** 2 + sF2 ** 2)
        sHelI = HelI * np.sqrt((sFHeI / FHeI) ** 2 + (sden / (F1 + F2)) ** 2)

        return HelI, sHelI

    def _calculate_nai(self, waves: np.ndarray, fluxes: np.ndarray,
                       errors: np.ndarray):
        """Calculate NaI D1/D2 activity indicator.

        Parameters
        ----------
        waves : numpy.ndarray
            Wavelength array
        fluxes : numpy.ndarray
            Flux array
        errors : numpy.ndarray
            Error array

        Returns
        -------
        nai_d1d2 : float
            NaI D1+D2 value
        nai_d1d2_error : float
            Error on NaI D1+D2
        """
        # NaI D1 line
        D1, sD1 = get_line_flux(waves, fluxes, NaID1, 1,
                                filt='square', error=errors)

        # NaI D2 line
        D2, sD2 = get_line_flux(waves, fluxes, NaID2, 1,
                                filt='square', error=errors)

        # Continuum L (left)
        L, sL = get_line_flux(waves, fluxes, 5805, 10,
                              filt='square', error=errors)

        # Continuum R (right)
        R, sR = get_line_flux(waves, fluxes, 6090, 20,
                              filt='square', error=errors)

        NaID1D2 = (D1 + D2) / (R + L)
        sNanum = np.sqrt(sD1 ** 2 + sD2 ** 2)
        sNaden = np.sqrt(sL ** 2 + sR ** 2)
        sNaID1D2 = NaID1D2 * np.sqrt((sNanum / (D1 + D2)) ** 2 +
                                      (sNaden / (R + L)) ** 2)

        return NaID1D2, sNaID1D2

    def _log_step(self, message: str, **kwargs):
        """Log processing step and call progress callback.

        Parameters
        ----------
        message : str
            Step description
        **kwargs
            Additional metadata
        """
        # Format message with kwargs for clean logging
        if kwargs:
            # Extract filename if present and make it more readable
            if 'filename' in kwargs:
                import os
                kwargs['filename'] = os.path.basename(kwargs['filename'])

            # Create clean message with key=value pairs
            extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} ({extras})"
        else:
            full_message = message

        self.logger.info(full_message)
        if self.progress_callback:
            self.progress_callback(message, **kwargs)
