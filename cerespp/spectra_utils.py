"""Spectra utils.

Various utilities for spectra.

Author: Jose Vines
"""
import copy
import os

import astropy.constants as const
import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from tqdm import tqdm

from .crosscorr import ccf, ccf_fit


def feros_velocity_correction(data, rv, create_fits=False, header=None, out=''):
    """Radial velocity correction for a FEROS spectrum.

    Parameters
    ----------
    data : array_like
        An array shaped (2, ord, N) where the first entry are the wavelengths,
        the second is the deblazed continuum normalized flux.
        Ord is the number of echelle orders and N the number of data

    rv : float
        The radial velocity in m/s

    create_fits : bool, optional
        True to save a fits file with the result.

    out : str, optional
        The location where to save the rest_frame spectra.

    Returns
    -------
    wavelength : array_like
        An array with the rest frame wavelengths.

    flux : array_like
        An array with the corresponding fluxes.

    """
    # Read fits file
    #     hdul = fits.open(spec)
    # Extract RV
    #     if not rv:
    #         rv = hdul[0].header['RV'] * u.km / u.s
    #         rv = rv.to(u.m / u. s)
    # Create gamma
    beta = rv / const.c
    gamma = 1 + beta.value
    # Extract wavelength per order
    wave = data[0, :, :]
    # Extract flux per order
    flux = data[1, :, :]
    # Extract the error of each order
    error = data[2, :, :]
    # Extract the snr of each order
    snr = data[3, :, :]
    orders = wave.shape[0]
    wave_rest = copy.deepcopy(wave)
    # Move spectra to rest frame
    for o in range(orders):
        wave_rest[o, :] /= gamma
    if create_fits:
        # Create new fits file
        date = header['HIERARCH SHUTTER START DATE'].split('-')
        ut = header['HIERARCH SHUTTER START UT'].split(':')
        out += header['HIERARCH TARGET NAME'] + '_'
        for d in date:
            out += d
        out += '_UT'
        for u in ut:
            out += u
        out += '_rest_frame.fits'
        hdu = fits.PrimaryHDU(np.stack((wave_rest, flux, error, snr)),
                              header=header)
        try:
            hdu.writeto(out)
        except OSError:
            os.remove(out)
            hdu.writeto(out)
    return wave_rest, flux


def velocity_correction(instrument, spec_list, rvs=[]):
    """Radial velocity correction for a list of spectra.

    Parameters
    ----------
    instrument : str
        The instrument with which the spectra was obtained.
    spec_list : array_like
        An array with filenames pointing to the fits files.

    """
    if instrument.lower() == 'feros':
        corrector = feros_velocity_correction
    if not rvs:
        for spec in tqdm(spec_list, desc='Spectra'):
            corrector(spec, True)
    else:
        for spec, rv in tqdm(zip(spec_list, rvs),
                             desc='Spectra', total=len(spec_list)):
            corrector(spec, True, rv)
    pass


def median_combine(spec_list, nord=None, plx=None):
    """Median combine rest frame spectra.

    Parameters
    ----------
    spec_list : array_like
        Array with spectra files.
    nord : int, optional
        Number of echelle orders.
    plx : float, optional
        Target's parallax.

    """
    wavelengths = []
    fluxes = []
    header = fits.open(spec_list[0])[0].header
    targ_name = header['HIERARCH TARGET NAME']
    ra = header['HIERARCH RA']
    dec = header['HIERARCH DEC']
    inst = header['INST']
    if nord is None:
        nord = header['NAXIS2']
    for o in tqdm(range(nord), desc='Order'):
        combiner = []
        for spec in spec_list:
            hdul = fits.open(spec)
            flux = hdul[0].data[1, o, :]
            wave = hdul[0].data[0, o, :]
            combiner.append(flux)
            hdul.close()
        combiner = np.array(combiner)
        combined = np.median(combiner, axis=0)
        fluxes.append(combined)
        wavelengths.append(wave)
    final_waves = np.vstack(wavelengths)
    final_fluxes = np.vstack(fluxes)
    final_out = np.stack([final_waves, final_fluxes])
    out = targ_name + '_stacked.fits'
    hdr = fits.Header()
    hdr['NAME'] = targ_name
    hdr['PLX'] = plx
    hdr['RA (deg)'] = ra
    hdr['DEC (deg)'] = dec
    hdr['INST'] = inst
    hdu = fits.PrimaryHDU(final_out, header=hdr)
    try:
        hdu.writeto(out)
    except OSError:
        os.remove(out)
        hdu.writeto(out)
    pass


def median_combine_1d(spec_list, plx=None):
    """Median combine 1d rest frame spectra.

    Parameters
    ----------
    spec_list : array_like
        Array with spectra files.
    plx : float, optional
        Target's parallax.

    """
    combiner = []
    header = fits.open(spec_list[0])[0].header
    wave = fits.open(spec_list[0])[0].data[0, :]
    new_w = np.linspace(wave[0], wave[-1], len(wave))
    targ_name = header['HIERARCH TARGET NAME']
    ra = header['HIERARCH RA (deg)']
    dec = header['HIERARCH DEC (deg)']
    inst = header['INST']
    for spec in spec_list:
        hdul = fits.open(spec)
        flux = hdul[0].data[1, :]
        wave = hdul[0].data[0, :]
        spl = interp1d(wave, flux, fill_value=0, bounds_error=False)
        combiner.append(spl(new_w))
        hdul.close()
    combiner = np.array(combiner)
    combined = np.median(combiner, axis=0)
    final_out = np.stack([new_w, combined])
    out = targ_name + '_1d_stacked.fits'
    hdr = fits.Header()
    hdr['HIERARCH TARGET NAME'] = targ_name
    hdr['HIERARCH PLX'] = plx
    hdr['HIERARCH RA (deg)'] = ra
    hdr['HIERARCH DEC (deg)'] = dec
    hdr['HIERARCH INST'] = inst
    hdu = fits.PrimaryHDU(final_out, header=hdr)
    try:
        hdu.writeto(out)
    except OSError:
        os.remove(out)
        hdu.writeto(out)
    pass


def merge_echelle(data, header, out='', save=False):
    """Merge echelle orders."""
    waves = np.array([])
    fluxes = np.array([])
    errors = np.array([])
    sn = np.array([])

    next_start = 0

    for i in range(data.shape[1] - 1, 0, -1):
        wave_current = data[0, i, :]
        wave_next = data[0, i - 1, :]
        flux_current = data[1, i, :]
        flux_next = data[1, i - 1, :]
        err_current = data[2, i, :]
        err_next = data[2, i - 1, :]
        sn_current = data[3, i, :]
        sn_next = data[3, i - 1, :]

        spl_current = interp1d(wave_current, sn_current)
        spl_next = interp1d(wave_next, sn_next)

        wav = np.linspace(wave_next[0], wave_current[-1], 1000)

        w = wav[np.argmin(abs(spl_current(wav) - spl_next(wav)))]

        cur_end = np.where(abs(wave_current - w) < 0.1)[0][0]

        wc = wave_current[next_start:cur_end]

        fc = flux_current[next_start:cur_end]

        erc = err_current[next_start:cur_end]

        snc = sn_current[next_start:cur_end]

        waves = np.concatenate((waves, wc))
        fluxes = np.concatenate((fluxes, fc))
        errors = np.concatenate((errors, erc))
        sn = np.concatenate((sn, snc))

        next_start = np.where(abs(wave_next - w) < 0.1)[0][0]

    waves = np.concatenate((waves, wave_next[next_start:]))
    fluxes = np.concatenate((fluxes, flux_next[next_start:]))
    errors = np.concatenate((errors, err_next[next_start:]))
    sn = np.concatenate((sn, sn_next[next_start:]))

    if save:
        prod_out = np.stack([waves, fluxes, errors, sn])

        targ_name = header['HIERARCH TARGET NAME']
        ra = header['HIERARCH RA']
        dec = header['HIERARCH DEC']
        inst = header['INST']

        hdr = fits.Header()
        hdr['HIERARCH TARGET NAME'] = targ_name
        hdr['HIERARCH RA (deg)'] = ra
        hdr['HIERARCH DEC (deg)'] = dec
        hdr['HIERARCH INST'] = inst

        hdu = fits.PrimaryHDU(prod_out, header=hdr)

        if not out:
            out = targ_name
        else:
            date = header['HIERARCH SHUTTER START DATE'].split('-')
            ut = header['HIERARCH SHUTTER START UT'].split(':')
            out += header['HIERARCH TARGET NAME'] + '_'
            for d in date:
                out += d
            out += '_UT'
            for u in ut:
                out += u
        out += '_1d_rest_frame.fits'
        try:
            hdu.writeto(out)
        except OSError:
            os.remove(out)
            hdu.writeto(out)

    return waves, fluxes, errors, sn


def correct_to_rest(data, mask='G2'):
    """Correct the spectra to rest frame and return wavelength and flux."""
    ccf_arr = []
    for o in range(data.shape[1] - 1, 0, -1):
        wave = data[0, o, :]
        flux = data[5, o, :]
        rv_arr, cc = ccf(wave, flux, mask=mask, drv=0.05)
        ccf_arr.append(cc)
    ccf_arr = np.array(ccf_arr)
    med_ccf = np.median(ccf_arr, axis=0)
    _, rv, _, _ = ccf_fit(rv_arr, med_ccf)

    w, f = feros_velocity_correction(
        data[[0, 5, 4, 8], :, :],
        rv * 1000,
        False,
    )

    return w, f
