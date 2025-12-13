# Ceres-plusplus

This package was written as an extension to the CERES reduction pipeline
(https://github.com/rabrahm/ceres) in the sense that it takes spectra reduced
by it and extracts some activity indicators (CCF FWHM, BIS, CONTRAST) and
calculates others (S index, Ha, HeI, NaID1D2)

It's been tested to work on FEROS and FIDEOS spectra. Feel free to use it with
other instruments and let me know if it works :)

## New in Version 1.3.0

Version 1.3.0 introduces significant improvements for integration with microservice architectures while maintaining 100% backward compatibility.

### Single-File Processing API

Process individual FITS files with granular logging and structured results:

```python
import cerespp

result = cerespp.process_single_file(
    'spectrum.fits',
    output_dir='results/',
    mask='G2',
    save=True  # Save 1D merged spectrum
)

print(f"S-index: {result.s_index:.3f} ± {result.s_index_error:.3f}")
print(f"1D spectrum saved to: {result.spectrum_1d_path}")
```

### Progress Callbacks

Monitor processing steps in real-time:

```python
def my_callback(step, **kwargs):
    print(f"Current step: {step}")

result = cerespp.process_single_file(
    'spectrum.fits',
    output_dir='results/',
    progress_callback=my_callback
)
```

### Structured Results

Results are returned as structured dataclasses with convenient methods:

```python
# Access individual fields
print(f"BJD: {result.bjd}")
print(f"RV: {result.rv} km/s")

# Convert to JSON-serializable dictionary
data = result.to_dict()
```

### Enhanced CLI

New command-line interface supports both single-file and bulk processing:

```bash
# New: Process single file with verbose logging
cerespp --file spectrum.fits --output results/ --save-1d --verbose

# Legacy: Bulk processing (still fully supported)
cerespp --files *.fits --output results.dat --mask G2
```

### Backward Compatibility

All existing code continues to work exactly as before:

```python
# This still works identically to previous versions
activities, header = cerespp.get_activities(
    files=['s1.fits', 's2.fits'],
    out='results.dat',
    mask='G2'
)
```

See the [API documentation](docs/api.md) for complete details and the [CHANGELOG](CHANGELOG.md) for all changes.

## Installation

You can try running `pip install cerespp`

If that fails you can clone the repository with

```bash
$ git clone https://github.com/jvines/Ceres-plusplus
$ cd Ceres-plusplus
$ python setup.py install
```

## Dependencies

Ceres-plusplus depends on the following packages:

- numpy ([https://numpy.org/](https://numpy.org/))
- scipy ([https://www.scipy.org/](https://www.scipy.org/))
- matplotlib (for plotting, but it's optional for the core functionality) ([https://matplotlib.org/](https://matplotlib.org/))
- astropy ([https://www.astropy.org/](https://www.astropy.org/))
- PyAstronomy ([https://pyastronomy.readthedocs.io/en/latest/](https://pyastronomy.readthedocs.io/en/latest/))
- tqdm ([https://tqdm.github.io/](https://tqdm.github.io/))
- termcolor ([https://pypi.org/project/termcolor/](https://pypi.org/project/termcolor/))

## Usage

Usage is simple, start by importing `cerespp`, optionally you can use `glob` to
fetch the files. After importing (and having ready your files) the
`get_activities` function, grab a coffee, and wait for your indicators!.

Below there's an example script

```python
import cerespp
import glob

files = glob.glob('path/to/fits/files/*.fits')
act, header = cerespp.get_activities(files, 'output/path/filename.dat')
```

Here `files` is a list with the fits files to process, the output `act` and
`header` are the activities and the header of the file (i.e. the names of the
columns). `cerespp` automatically saves the output in a file in the desired
location, but if you need the output on the session you're working in
(in a jupyter notebook, for example), that's what `act` and `header` are for ;)

## Plotting

`cerespp` offers some plotting tools to visually check things! The most
important ones are plots showing the activity lines and their surroundings.
Creating these is easy:

```python
import cerespp
import glob

# These are the available lines. You can choose which ones to plot here 
lines = ['CaHK', 'Ha', 'HeI', 'NaID1D2'] 

files = glob.glob('path/to/fits/files/*.fits')

# This function creates the plots from a fits file directly
cerespp.line_plot_from_file(files[0], lines, 'output/path/', 'starname')
```

There's a notebook exemplifying the usage in the examples folder!

## How it works

`cerespp` first calculates a radial velocity to correct the spectrum to
rest-frame, after this has been done it extracts the available data from the
fits headers (CCF FWHM, BIS, CONTRAST) and finally it merges the echelle orders
and computes the activity indicators!

The radial velocity is computed using the standard cross-correlation function
method, and thus you can specify which mask to use with the `mask` keyword in
`get_activities`. Available masks are `G2, K0, K5,` and `M2`.
