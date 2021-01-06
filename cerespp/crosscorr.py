"""Crosscorr.

This module calculates the cross-correlation function of a spectrum with a
binary mask, and fits a gaussian to the resulting CCF.

Author: Jose Vines
"""
import numpy as np
from PyAstronomy import pyasl
from scipy.optimize import curve_fit

from .utils import gauss_fit
from .constants import masksdir


def ccf(wave, flux, mask='G2', rvmin=-300, rvmax=300, drv=0.1):
    """Calculate the cross-correlation function.

    Parameters
    ----------
    wave: array_like
        The wavelength array of the spectrum.
    flux: array_like
        The flux array of the spectrum.
    mask: str, optional
        The binary mask to use. Options are G2, K0, K5, and M2. Default is G2.
    rvmin: float, optional
        The minimum radial velocity to test, in km/s. Default is -300.
    rvmax: float, optional
        The maximum radial velocity to test, in km/s. Default is 300.
    drv: float, optional
        The step in velocity space for the crosscorr algorithm.

    Returns
    -------
    rv_temp: array_like
        The radial velocities tested.
    cc: array_like
        The median normalized CCF.
    """
    # read mask, call crosscorr
    x1 = np.arange(wave[0] - 200, wave[0], wave[1] - wave[0])
    x2 = np.arange(wave[-1], wave[-1] + 200, wave[-1] - wave[-2])
    wtem = np.hstack([x1, wave, x2])

    lines1, lines2, flux_l = np.loadtxt(f'{masksdir}/{mask}.mas', unpack=True)
    lines_idx = np.where((lines1 > wave[0]) & (lines2 < wave[-1]))[0]
    lines1_new = lines1[lines_idx]
    lines2_new = lines2[lines_idx]
    flux_l_new = flux_l[lines_idx]

    ftem = np.zeros(wtem.size)

    for i in range(len(flux_l_new)):
        indices = np.where((wtem >= lines1_new[i]) & (wtem <= lines2_new[i]))
        if indices[0].size > 0:
            ftem[indices[0]] = flux_l_new[i]

    rv_temp, cc = pyasl.crosscorrRV(wave, flux, wtem, ftem, rvmin, rvmax, drv)
    return rv_temp, cc / np.median(cc)


def ccf_fit(rvs, cc):
    """Fit a gaussian to the CCF with curve_fit.

    Parameters
    ----------
    rvs: array_like
        The RV array
    cc: array_like
        The cross-correlation function.
    """
    est = np.argmin(cc)
    rv_min = rvs[est]
    cc_min = cc[est]
    p0 = [cc_min, rv_min, 1., 1.]
    popt, _ = curve_fit(gauss_fit, rvs, cc, p0=p0)
    return popt






