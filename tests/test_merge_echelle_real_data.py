"""Compare optimized merge_echelle against the original algorithm on real data.

Runs both implementations on an actual CERES-reduced FEROS spectrum and
checks that the outputs are nearly identical (small differences expected
from linear vs cubic interpolation at order boundaries).
"""
import os
import numpy as np
import pytest
from scipy.interpolate import interp1d
from astropy.io import fits


REAL_FITS = "/data/spectra/spectra/2018-02-11_red/proc/HATS699-034_20180212_UT07-36-49.727_sp.fits"


def _merge_echelle_original(data, header):
    """Original merge_echelle implementation (pre-optimization) for comparison."""
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

    return waves, fluxes, errors, sn


@pytest.fixture(scope="module")
def real_data():
    """Load the real FITS file and build the 4-row merge input."""
    if not os.path.exists(REAL_FITS):
        pytest.skip(f"Real FITS file not available: {REAL_FITS}")
    hdul = fits.open(REAL_FITS)
    full_data = hdul[0].data  # (11, 25, 4096)
    header = hdul[0].header
    # merge_echelle expects (4, n_orders, n_pixels): wave, flux, error, sn
    # In the processor, it's called with: np.stack((w, f, data[2], data[8]))
    # For a standalone test, use rows 0,5,6,8 mapped to 0,1,2,3
    data = np.stack([
        full_data[0, :, :],   # wavelength
        full_data[5, :, :],   # deblazed flux
        full_data[6, :, :],   # error
        full_data[8, :, :],   # S/N
    ])
    hdul.close()
    return data, header


class TestRealDataComparison:
    """Compare old and new merge_echelle on real FEROS data."""

    def test_wavelength_difference_small(self, real_data):
        """Crossover points may shift slightly; total wavelength difference should be tiny."""
        from cerespp.spectra_utils import merge_echelle

        data, header = real_data
        w_old, _, _, _ = _merge_echelle_original(data, header)
        w_new, _, _, _, _ = merge_echelle(data, header)

        # Lengths may differ by a few pixels due to searchsorted vs np.where
        len_diff = abs(len(w_old) - len(w_new))
        assert len_diff < 50, f"Length differs by {len_diff} pixels (expected <50)"

        # Compare overlapping range
        min_len = min(len(w_old), len(w_new))
        # Both should cover nearly the same range
        assert abs(w_old[0] - w_new[0]) < 1.0, "Start wavelength differs by >1 Angstrom"
        assert abs(w_old[-1] - w_new[-1]) < 1.0, "End wavelength differs by >1 Angstrom"

    def test_both_monotonically_increasing(self, real_data):
        """Both old and new must produce strictly increasing wavelengths."""
        from cerespp.spectra_utils import merge_echelle

        data, header = real_data
        w_old, _, _, _ = _merge_echelle_original(data, header)
        w_new, _, _, _, _ = merge_echelle(data, header)

        assert np.all(np.diff(w_old) > 0), "Original has non-monotonic wavelengths"
        assert np.all(np.diff(w_new) > 0), "Optimized has non-monotonic wavelengths"

    def test_flux_correlation(self, real_data):
        """Flux arrays should be highly correlated (same data, slightly different boundaries)."""
        from cerespp.spectra_utils import merge_echelle

        data, header = real_data
        _, f_old, _, _ = _merge_echelle_original(data, header)
        w_new, f_new, _, _, _ = merge_echelle(data, header)
        w_old, _, _, _ = _merge_echelle_original(data, header)

        # Interpolate new onto old wavelength grid for comparison
        f_new_interp = np.interp(w_old, w_new, f_new)

        # Mask edges (first/last 100 pixels) where boundary effects are largest
        mask = slice(100, -100)
        corr = np.corrcoef(f_old[mask], f_new_interp[mask])[0, 1]
        assert corr > 0.999, f"Flux correlation {corr:.6f} too low (expected >0.999)"

    def test_no_nans_real_data(self, real_data):
        """Optimized merge must produce no NaNs on real data."""
        from cerespp.spectra_utils import merge_echelle

        data, header = real_data
        w, f, e, s, _ = merge_echelle(data, header)
        assert not np.any(np.isnan(w)), "NaN in wavelengths"
        assert not np.any(np.isnan(f)), "NaN in fluxes"
        assert not np.any(np.isnan(e)), "NaN in errors"
        assert not np.any(np.isnan(s)), "NaN in S/N"

    def test_performance_improvement(self, real_data):
        """Optimized version should be faster (or at least not slower)."""
        import time
        from cerespp.spectra_utils import merge_echelle

        data, header = real_data
        n_runs = 20

        # Warm up
        _merge_echelle_original(data, header)
        merge_echelle(data, header)

        t0 = time.perf_counter()
        for _ in range(n_runs):
            _merge_echelle_original(data, header)
        old_time = (time.perf_counter() - t0) / n_runs

        t0 = time.perf_counter()
        for _ in range(n_runs):
            merge_echelle(data, header)
        new_time = (time.perf_counter() - t0) / n_runs

        speedup = old_time / new_time
        print(f"\nOld: {old_time*1000:.1f}ms  New: {new_time*1000:.1f}ms  Speedup: {speedup:.2f}x")
        # Optimized should be at least as fast (allow 10% margin for noise)
        assert new_time < old_time * 1.1, f"New version slower: {new_time:.4f}s vs {old_time:.4f}s"
