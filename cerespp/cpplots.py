import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import triang
from termcolor import colored
from astropy.io import fits

from .constants import *
from .utils import gauss_fit
from .spectra_utils import correct_to_rest, merge_echelle


def __ensure_png_pdf(png, pdf):
    if not png and not pdf:
        print(
            colored('Warning! No extension selected! Reverting to png!', 'red')
        )
        return False
    return True


def __setup_ticks(ax):
    """Common tick setup"""
    ax.tick_params(
        axis='both', which='major',
        labelsize=tick_labelsize
    )
    for tick in ax.get_yticklabels():
        tick.set_fontname(fontname)
    for tick in ax.get_xticklabels():
        tick.set_fontname(fontname)
    return ax


def ccf_plot(name, rvs, cc):
    """Create a plot of the CCF."""
    f, ax = plt.subplots(figsize=(12, 8))
    ax.plot(rvs, cc, lw=0.7, color='k')
    ax.set_ylabel('CCF',
                  fontsize=fontsize,
                  fontname=fontname
                  )
    ax.set_xlabel('RV (km/s)',
                  fontsize=fontsize,
                  fontname=fontname
                  )
    ax = __setup_ticks(ax)
    plt.savefig(name + '_ccf.pdf', bbox_inches='tight')


def ccf_gauss_plot(name, rvs, cc, amp, rv, sig, off):
    """Create a plot of the CCF with a gaussian fit."""
    f, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(rvs, cc, s=10, marker='.', color='k')
    ax.plot(rvs, gauss_fit(rvs, amp, rv, sig, off))
    ax.set_xlim([rv - 30, rv + 30])
    ax.set_ylabel('CCF',
                  fontsize=fontsize,
                  fontname=fontname
                  )
    ax.set_xlabel('RV (km/s)',
                  fontsize=fontsize,
                  fontname=fontname
                  )
    ax = __setup_ticks(ax)
    plt.savefig(name + '_ccf_fit.pdf', bbox_inches='tight')


def line_plot_from_file(filename, lines, out, name, png=True, pdf=False,
                        verbose=False):
    """Create a plot showing the selected lines.

    Parameters
    ----------
    filename: str
        The file name of the spectrum.
    lines: str, array_like
        A string with the line to plot or an array with the linesto plot.
    out: str
        The output location for the plot.
    name: str
        The name of the object.
    png: bool, optional
        Set to True to output plot in png. Default is True.
    pdf: bool, optional
        Set to True to output plot in pdf. Default is False
    verbose: bool, optional
        Enable prints.
    """
    hdul = fits.open(filename)
    data = hdul[0].data
    if verbose:
        print('Correcting spectrum to rest frame. (This could take a while)')
    w, f = correct_to_rest(data)
    prod = np.stack((w, f, data[4, :, :], data[8, :, :]))
    if verbose:
        print('Merging echelle spectra.')
    waves, fluxes, _, _ = merge_echelle(prod, hdul[0].header)
    line_plot(waves, fluxes, lines, out, name, png=png, pdf=pdf)


def line_plot(waves, fluxes, lines, out, name, png=True, pdf=False,
              verbose=False):
    """Create a plot showing the selected lines.

    Parameters
    ----------
    waves: array_like
        The wavelength array.
    fluxes: array_like
        The flux array.
    lines: str, array_like
        A string with the line to plot or an array with the lines to plot.
    out: str
        The output location for the plot.
    name: str
        The name of the object.
    png: bool, optional
        Set to True to output plot in png. Default is True.
    pdf: bool, optional
        Set to True to output plot in pdf. Default is False
    verbose: bool, optional
        Enable prints.
    """
    if isinstance(lines, str):  # check if lines is a str or a list/array
        lines = [lines]

    png = png if __ensure_png_pdf(png, pdf) else True
    for line in lines:
        if verbose:
            print(f'Plotting line {line}')
        f, ax = plt.subplots(figsize=(20, 10))
        ax.plot(waves, fluxes, c='k', lw=.85)

        if line == 'CaHK':
            ax = CaHK_plot(ax)
        elif line == 'Ha':
            ax = Ha_plot(ax)
        elif line == 'HeI':
            ax = HeI_plot(ax)
        elif line == 'NaID1D2':
            ax = NaID1D2_plot(ax)
        lims = ax.get_xlim()
        i = np.where((waves > lims[0]) & (waves < lims[1]))[0]
        ax.set_ylim(fluxes[i].min() * .95, fluxes[i].max() * 1.25)
        if png:
          plt.savefig(f'{out}/{name}_{line}.png', bbox_inches='tight')
        if pdf:
          plt.savefig(f'{out}/{name}_{line}.pdf', bbox_inches='tight')


def CaHK_plot(ax):
    """Plot the CaHK lines and bandpasses."""
    w = triang(1001, True)
    ax.plot(np.linspace(CaK - 1.19, CaK + 1.19, len(w)), w, c='tab:blue', lw=2)
    ax.plot(np.linspace(CaH - 1.19, CaH + 1.19, len(w)), w, c='tab:blue', lw=2)

    ax.axvspan(CaV - 10, CaV + 10, color='tab:blue', alpha=.5)
    ax.axvspan(CaR - 10, CaR + 10, color='tab:blue', alpha=.5)

    ax.axvline(CaK, c='red', ls='dashed')
    ax.axvline(CaH, c='red', ls='dashed')

    ax.set_xlim(3880, 4020)

    ax.set_title(r'Ca$_{\rm II}$ H+K',
                 fontname=fontname,
                 fontsize=fontsize
                 )
    ax.set_xlabel(r'$\lambda~[\AA]$',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    ax.set_ylabel('Normalized flux',
                  fontname=fontname,
                  fontsize=fontsize
                  )

    return __setup_ticks(ax)


def Ha_plot(ax):
    """Plot the Ha line and bandpass."""
    ax.axvspan(Ha - 0.678, Ha + 0.678, color='tab:blue', alpha=.5)
    ax.axvspan(6545.495, 6556.245, color='tab:blue', alpha=.5)
    ax.axvspan(6575.934, 6584.684, color='tab:blue', alpha=.5)
    ax.axvline(Ha, color='red', ls='dashed')

    ax.set_xlim(6544.495, 6585.684)

    ax.set_title(r'H$_{\alpha}$',
                 fontname=fontname,
                 fontsize=fontsize
                 )
    ax.set_xlabel(r'$\lambda~[\AA]$',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    ax.set_ylabel('Normalized flux',
                  fontname=fontname,
                  fontsize=fontsize
                  )

    ax.tick_params(
        axis='both', which='major',
        labelsize=tick_labelsize
    )

    return __setup_ticks(ax)


def HeI_plot(ax):
    """Plot the HeI line and bandpass."""
    ax.axvspan(HeI - .2, HeI + .2, color='tab:blue', alpha=.5)
    ax.axvspan(5874.0, 5875.0, color='tab:blue', alpha=.5)
    ax.axvspan(5878.5, 5879.5, color='tab:blue', alpha=.5)

    ax.axvline(HeI, color='red', ls='dashed')

    ax.set_xlim(5873.75, 5879.75)

    ax.set_title(r'He$_{\rm I}$',
                 fontname=fontname,
                 fontsize=fontsize
                 )
    ax.set_xlabel(r'$\lambda~[\AA]$',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    ax.set_ylabel('Normalized flux',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    return __setup_ticks(ax)


def NaID1D2_plot(ax):
    """Plot the NaID1 and NaID2 lines and bandpasses."""
    ax.axvspan(NaID1 - .5, NaID1 + .5, color='tab:blue', alpha=.5)
    ax.axvspan(NaID2 - .5, NaID2 + .5, color='tab:blue', alpha=.5)
    ax.axvspan(5800, 5810, color='tab:blue', alpha=.5)
    ax.axvspan(6080, 6100, color='tab:blue', alpha=.5)

    ax.axvline(NaID1, color='red', ls='dashed')
    ax.axvline(NaID2, color='red', ls='dashed')

    ax.set_xlim(5790, 6110)

    ax.set_title(r'Na$_{\rm I}$ D1 D2',
                 fontname=fontname,
                 fontsize=fontsize
                 )
    ax.set_xlabel(r'$\lambda~[\AA]$',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    ax.set_ylabel('Normalized flux',
                  fontname=fontname,
                  fontsize=fontsize
                  )
    return __setup_ticks(ax)