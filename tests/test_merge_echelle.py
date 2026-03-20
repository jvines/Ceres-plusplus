"""Tests for the optimized merge_echelle function.

Verifies correctness of:
- List-based collection + single np.concatenate (replaces in-loop concat)
- np.interp for S/N crossover (replaces interp1d)
- np.searchsorted for index lookup (replaces np.where)
"""
import numpy as np
import pytest

from cerespp.spectra_utils import merge_echelle


def _make_echelle(n_orders=5, n_pixels=500, wave_start=4000.0,
                  order_span=200.0, overlap_frac=0.15):
    """Create synthetic echelle data with realistic overlapping orders.

    Returns data array shaped (4, n_orders, n_pixels) where:
      [0] = wavelength, [1] = flux, [2] = error, [3] = S/N

    Orders are arranged so that order 0 covers the reddest wavelengths
    and order n_orders-1 covers the bluest, matching FEROS echelle convention.
    Overlap region has ~overlap_frac fractional coverage between adjacent orders.
    """
    data = np.zeros((4, n_orders, n_pixels))
    step = order_span * (1 - overlap_frac)

    for i in range(n_orders):
        # Order index 0 = reddest, n_orders-1 = bluest
        idx = n_orders - 1 - i
        w0 = wave_start + i * step
        w1 = w0 + order_span
        wave = np.linspace(w0, w1, n_pixels)
        flux = 1.0 + 0.05 * np.sin(wave / 10)
        error = 0.01 * np.ones(n_pixels)
        # S/N peaks at center of order, drops at edges (realistic)
        center = (w0 + w1) / 2
        sn = 100 * np.exp(-0.5 * ((wave - center) / (order_span / 3)) ** 2)

        data[0, idx, :] = wave
        data[1, idx, :] = flux
        data[2, idx, :] = error
        data[3, idx, :] = sn

    return data


def _make_header():
    """Create a minimal FITS-like header dict for merge_echelle."""
    class FakeHeader(dict):
        def __getitem__(self, key):
            defaults = {
                'HIERARCH TARGET NAME': 'TestStar',
                'HIERARCH RA': 180.0,
                'HIERARCH DEC': -30.0,
                'INST': 'FEROS',
                'HIERARCH SHUTTER START DATE': '2025-01-15',
                'HIERARCH SHUTTER START UT': '08:30:00',
            }
            return defaults.get(key, super().__getitem__(key))

        def get(self, key, default=None):
            try:
                return self[key]
            except KeyError:
                return default

    return FakeHeader()


class TestMergeEchelleCorrectness:
    """Core correctness tests for the optimized merge_echelle."""

    def test_wavelengths_monotonically_increasing(self):
        """Merged wavelength array must be strictly increasing."""
        data = _make_echelle(n_orders=5)
        header = _make_header()
        waves, fluxes, errors, sn, _ = merge_echelle(data, header)
        diffs = np.diff(waves)
        assert np.all(diffs > 0), "Wavelengths must be strictly increasing"

    def test_output_covers_full_range(self):
        """Merged spectrum should cover from bluest to reddest order."""
        data = _make_echelle(n_orders=5)
        header = _make_header()
        waves, _, _, _, _ = merge_echelle(data, header)

        # Should start near the bluest order's start
        all_waves_min = data[0, :, :].min()
        all_waves_max = data[0, :, :].max()
        assert waves[0] >= all_waves_min
        assert waves[-1] <= all_waves_max
        # Coverage should span most of the total range
        coverage = (waves[-1] - waves[0]) / (all_waves_max - all_waves_min)
        assert coverage > 0.85, f"Coverage {coverage:.2f} is too low"

    def test_no_nans_in_output(self):
        """Output arrays should contain no NaN values."""
        data = _make_echelle(n_orders=5)
        header = _make_header()
        waves, fluxes, errors, sn, _ = merge_echelle(data, header)
        assert not np.any(np.isnan(waves))
        assert not np.any(np.isnan(fluxes))
        assert not np.any(np.isnan(errors))
        assert not np.any(np.isnan(sn))

    def test_all_outputs_same_length(self):
        """All four output arrays must have the same length."""
        data = _make_echelle(n_orders=5)
        header = _make_header()
        waves, fluxes, errors, sn, _ = merge_echelle(data, header)
        assert len(waves) == len(fluxes) == len(errors) == len(sn)

    def test_output_shorter_than_total_pixels(self):
        """Merged output should be shorter than sum of all pixels (overlaps removed)."""
        n_orders = 5
        n_pixels = 500
        data = _make_echelle(n_orders=n_orders, n_pixels=n_pixels)
        header = _make_header()
        waves, _, _, _, _ = merge_echelle(data, header)
        # With 15% overlap, merged should be significantly shorter than 5*500
        assert len(waves) < n_orders * n_pixels
        assert len(waves) > n_pixels  # But longer than a single order

    def test_flux_values_preserved(self):
        """Flux values in non-overlap regions should be unchanged from input."""
        data = _make_echelle(n_orders=3, n_pixels=500, overlap_frac=0.15)
        header = _make_header()
        waves, fluxes, _, _, _ = merge_echelle(data, header)

        # Check that flux values come from the original data
        # The middle portion of the reddest order should be untouched
        # (it's the first order processed, and its center is far from any crossover)
        reddest_order = 0  # index 0 = reddest
        center_start = 200
        center_end = 300
        order_wave = data[0, reddest_order, center_start:center_end]
        order_flux = data[1, reddest_order, center_start:center_end]

        # Find these wavelengths in the merged spectrum
        for w, f in zip(order_wave, order_flux):
            idx = np.searchsorted(waves, w)
            if 0 < idx < len(waves) - 1:
                # Check the nearest merged wavelength matches
                if abs(waves[idx] - w) < 1e-10:
                    assert abs(fluxes[idx] - f) < 1e-10, \
                        f"Flux mismatch at wave={w}"


class TestMergeEchelleEdgeCases:
    """Edge case tests."""

    def test_two_orders(self):
        """Minimum case: two orders should merge cleanly."""
        data = _make_echelle(n_orders=2)
        header = _make_header()
        waves, fluxes, errors, sn, _ = merge_echelle(data, header)
        assert len(waves) > 0
        assert np.all(np.diff(waves) > 0)

    def test_many_orders(self):
        """Stress test with many orders (typical FEROS has ~39)."""
        data = _make_echelle(n_orders=39, n_pixels=4096, overlap_frac=0.10)
        header = _make_header()
        waves, fluxes, errors, sn, _ = merge_echelle(data, header)
        assert np.all(np.diff(waves) > 0)
        assert len(waves) == len(fluxes)

    def test_small_overlap(self):
        """Orders with minimal overlap should still merge."""
        data = _make_echelle(n_orders=3, overlap_frac=0.05)
        header = _make_header()
        waves, _, _, _, _ = merge_echelle(data, header)
        assert np.all(np.diff(waves) > 0)

    def test_save_false_returns_none_path(self):
        """When save=False, output_path should be None."""
        data = _make_echelle(n_orders=3)
        header = _make_header()
        _, _, _, _, output_path = merge_echelle(data, header, save=False)
        assert output_path is None

    def test_deterministic(self):
        """Same input should produce identical output."""
        data = _make_echelle(n_orders=5)
        header = _make_header()
        w1, f1, e1, s1, _ = merge_echelle(data, header)
        w2, f2, e2, s2, _ = merge_echelle(data, header)
        np.testing.assert_array_equal(w1, w2)
        np.testing.assert_array_equal(f1, f2)
