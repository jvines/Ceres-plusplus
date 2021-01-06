"""cerespp.

Main routine for ceres plusplus.

Author: Jose Vines
"""
import numpy as np
from astropy.io import fits
from tqdm import tqdm

from .spectra_utils import correct_to_rest, merge_echelle
from .utils import get_line_flux
from .constants import *


def get_activities(files, out, mask='G2', save=False):
    """Main function.

    Parameters
    ----------
    files: array_like
        An array or list with the spectra filenames.
    out: str
        The output directory for the results.
    save: bool, optional
        Set to True to save the merged echelle spectra. Default is False.

    Returns
    -------
    data: array_like
        An array with the activity indices.
    header: array_like
        An array with the activity indices identifiers.

    """
    nofwhm = False

    # Activity holders
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

    for fname in tqdm(files):
        hdul = fits.open(fname)
        data = hdul[0].data

        bjd.append(hdul[0].header['BJD_OUT'])  # Extract BJD
        bis.append(hdul[0].header['BS'])  # Extract BIS
        bis_err.append(hdul[0].header['BS_E'])  # Extract BIS error
        try:
            fwhm.append(hdul[0].header['FWHM'])  # Try and get the FWHM
            # This calculates the error on the FWHM, inspired by the RV error
            # Calculation from the ceres paper.
            fwhm_err.append(hdul[0].header['DISP'] / hdul[0].header['SNR'])
        except KeyError:  # if the FWHM is not in the header for some reason..
            nofwhm = True
        contrast.append(hdul[0].header['XC_MIN'])

        w, f = correct_to_rest(data, mask=mask)

        prod = np.stack((w, f, data[4, :, :], data[8, :, :]))

        waves, fluxes, errors, sn = merge_echelle(prod, hdul[0].header,
                                                  out=out, save=save)

        # Get S index
        # First is CaV
        NV, sNV = get_line_flux(waves, fluxes, CaV, 20, filt='square',
                                error=errors)

        # Now CaR
        NR, sNR = get_line_flux(waves, fluxes, CaR, 20,
                                filt='square', error=errors)

        # Now CaK
        NK, sNK = get_line_flux(waves, fluxes, CaK, 1.09,
                                filt='triangle', error=errors)

        # Now CaH
        NH, sNH = get_line_flux(waves, fluxes, CaH, 1.09,
                                filt='triangle', error=errors)

        S = (NH + NK) / (NR + NV)
        sSnum = np.sqrt(sNH ** 2 + sNK ** 2)
        sSden = np.sqrt(sNV ** 2 + sNR ** 2)
        sS = np.sqrt((sSnum / (NH + NK)) ** 2 + (sSden / (NR + NV)) ** 2)

        s_indices.append(S)
        s_err.append(sS)

        # Now Halpha
        FHa, sFHa = get_line_flux(waves, fluxes, Ha, 0.678,
                                  filt='square', error=errors)

        # Now F1
        F1, sF1 = get_line_flux(waves, fluxes, 6550.87,
                                10.75, filt='square', error=errors)

        # Now F2
        F2, sF2 = get_line_flux(waves, fluxes, 6580.309,
                                8.75, filt='square', error=errors)

        Halpha = FHa / (0.5 * (F1 + F2))
        sden = np.sqrt(sF1 ** 2 + sF2 ** 2)
        sHalpha = np.sqrt((sFHa / FHa) ** 2 + (sden / (F1 + F2)) ** 2)

        ha.append(Halpha)
        ha_err.append(sHalpha)

        # Now HeI
        FHeI, sFHeI = get_line_flux(waves, fluxes, HeI, 0.2,
                                    filt='square', error=errors)

        # Now F1
        F1, sF1 = get_line_flux(waves, fluxes, 5874.5,
                                0.5, filt='square', error=errors)

        # Now F2
        F2, sF2 = get_line_flux(waves, fluxes, 5879,
                                0.5, filt='square', error=errors)

        HelI = FHeI / (0.5 * (F1 + F2))
        sden = np.sqrt(sF1 ** 2 + sF2 ** 2)
        sHelI = np.sqrt((sFHeI / FHeI) ** 2 + (sden / (F1 + F2)) ** 2)

        hei.append(HelI)
        hei_err.append(sHelI)

        # Now NaI D1 D2
        D1, sD1 = get_line_flux(waves, fluxes, NaID1, 1,
                                filt='square', error=errors)

        D2, sD2 = get_line_flux(waves, fluxes, NaID2, 1,
                                filt='square', error=errors)

        L, sL = get_line_flux(waves, fluxes, 5805, 10, filt='square',
                              error=errors)

        R, sR = get_line_flux(waves, fluxes, 6090, 20, filt='square',
                              error=errors)

        NaID1D2 = (D1 + D2) / (R + L)
        sNanum = np.sqrt(sD1 ** 2 + sD2 ** 2)
        sNaden = np.sqrt(sL ** 2 + sR ** 2)
        sNaID1D2 = np.sqrt((sNanum / (D1 + D2)) ** 2 + (sNaden / (R + L)) ** 2)

        nai.append(NaID1D2)
        nai_err.append(sNaID1D2)

        if not nofwhm:
            header = 'bjd S e_S Halpha e_Halpha HeI'
            header += ' e_HeI NaID1D2 e_NaID1D2 BIS e_BIS FWHM e_FWHM CONTRAST'

            data = np.vstack(
                [
                    bjd,
                    s_indices, s_err,
                    ha, ha_err,
                    hei, hei_err,
                    nai, nai_err,
                    bis, bis_err,
                    fwhm, fwhm_err,
                    contrast
                ]
            ).T
        else:
            header = 'bjd S e_S Halpha e_Halpha HeI'
            header += ' e_HeI NaID1D2 e_NaID1D2 BIS e_BIS CONTRAST'

            data = np.vstack(
                [
                    bjd,
                    s_indices, s_err,
                    ha, ha_err,
                    hei, hei_err,
                    nai, nai_err,
                    bis, bis_err,
                    contrast
                ]
            ).T
        np.savetxt(
            f'{out}.dat', data, header=header)
    return data, header