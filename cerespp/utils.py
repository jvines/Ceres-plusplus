import numpy as np
from scipy.integrate import trapz
from scipy.interpolate import interp1d
from scipy.signal import triang
from scipy.stats import norm


def gauss_fit(r, a, mu, sig, off):
    """Wrapper for a gaussian function used in a fitting routine."""
    return off + a * norm.pdf(r, loc=mu, scale=sig)


def get_ini_end(x, mid, width):
    """Get initial and ending indices for a band with a given width."""
    ini = np.argmin(abs(x - (mid - width)))
    end = np.argmin(abs(x - (mid + width)))
    return ini, end


def get_response(line, width, filt='square'):
    """Instantiate a response filter and return filter width."""
    if filt == 'square':
        width /= 2
        w_resp = np.linspace(line - width, line + width, 1000)
        resp_f = interp1d(w_resp, np.ones(
            1000), bounds_error=False, fill_value=0)
    elif filt == 'triangle':
        tri = triang(999, True)
        w_resp = np.linspace(line - width, line + width, 999)
        resp_f = interp1d(w_resp, tri, bounds_error=False, fill_value=0)
    return resp_f, width


def get_line_flux(wavelength, flux, line, width, filt='square', error=None):
    """Calculate line flux with a given response filter.

    Accepted filter values are square or triangle, if triangle
    then the width will be taken as the FWHM of the filter bandpass.

    Also calculates error in flux if an error array is provided.

    To calculate the flux first a filter response function is created
    Then the flux is rebbined in the line width, convolved with the
    response filter and finally normalized by the integrated response
    function.
    """
    resp_f, width = get_response(line, width, filt)
    ini, end = get_ini_end(wavelength, line, width)
    w = np.linspace(line - width, line + width, (end - ini))
    intp = interp1d(wavelength[ini - 2:end + 2], flux[ini - 2:end + 2])
    intp_flux = intp(w)
    response = resp_f(w)
    integrated_flux = trapz(intp_flux * response, w) / trapz(response, w)
    if error is not None:
        num = (error[ini:end] * resp_f(wavelength[ini:end])) ** 2
        den = resp_f(wavelength[ini:end]) ** 2
        var = num.sum() / den.sum()
        sigma = np.sqrt(var)
        return integrated_flux, sigma
    return integrated_flux
