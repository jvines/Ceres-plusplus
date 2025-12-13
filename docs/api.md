# Ceres++ API Reference

## Core Functions

### `get_activities(files, out, mask='G2', save=False, logger=None, progress_callback=None)`

**Legacy bulk processing function** - processes multiple FITS files and returns activity indicators.

**Parameters:**
- `files` (list): List of paths to FITS files to process
- `out` (str): Output file path for results (`.dat` file)
- `mask` (str, optional): Spectral mask to use for CCF. Options: `'G2'`, `'K0'`, `'K5'`, `'M2'`. Default: `'G2'`
- `save` (bool, optional): Whether to save 1D merged spectra to FITS files. Default: `False`
- `logger` (StructuredLogger, optional): Custom logger instance. Default: creates default logger
- `progress_callback` (callable, optional): Function called on each processing step. Default: `None`

**Returns:**
- `activities` (numpy.ndarray): Array of activity indicators with columns:
  - BJD (Barycentric Julian Date)
  - RV (Radial Velocity)
  - BIS (Bisector Span)
  - FWHM (Full Width at Half Maximum)
  - CONTRAST (CCF Contrast)
  - S_index (Ca II H&K S-index)
  - S_index_error
  - Halpha (H-alpha index)
  - Halpha_error
  - HeI (He I index)
  - HeI_error
  - NaI_D1 (Na I D1 index)
  - NaI_D2 (Na I D2 index)
- `header` (list): Column names for the activity array

**Example:**
```python
import cerespp
import glob

files = glob.glob('spectra/*.fits')
activities, header = cerespp.get_activities(
    files,
    'results.dat',
    mask='K0',
    save=True
)
```

**Backward Compatibility:**
This function maintains 100% backward compatibility with previous versions. All existing code using `get_activities()` will continue to work unchanged.

---

### `process_single_file(filename, out, mask='G2', save=True, logger=None, progress_callback=None)`

**New in v1.3.0** - Process a single FITS file with granular logging and structured results.

**Parameters:**
- `filename` (str): Path to FITS file to process
- `out` (str): Output directory for results
- `mask` (str, optional): Spectral mask to use for CCF. Options: `'G2'`, `'K0'`, `'K5'`, `'M2'`. Default: `'G2'`
- `save` (bool, optional): Whether to save 1D merged spectrum to FITS file. Default: `True`
- `logger` (StructuredLogger, optional): Custom logger instance. Default: creates default logger
- `progress_callback` (callable, optional): Function called on each processing step. Default: `None`

**Returns:**
- `ProcessingResult`: Dataclass with structured results (see below)

**Example:**
```python
import cerespp

result = cerespp.process_single_file(
    'spectrum_2023-01-15.fits',
    output_dir='results/',
    mask='G2',
    save=True
)

print(f"S-index: {result.s_index:.3f} ± {result.s_index_error:.3f}")
print(f"RV: {result.rv:.2f} km/s")
print(f"1D spectrum saved to: {result.spectrum_1d_path}")
```

**With Progress Callback:**
```python
def progress_monitor(step, **kwargs):
    """Called on each processing step"""
    print(f"Current step: {step}")
    if 'filename' in kwargs:
        print(f"  File: {kwargs['filename']}")

result = cerespp.process_single_file(
    'spectrum.fits',
    'results/',
    progress_callback=progress_monitor
)
```

**Processing Steps:**
The function performs these steps (each triggers the progress callback):
1. Loading FITS file
2. Converting to rest frame
3. Merging echelle orders
4. Calculating S-index
5. Calculating H-alpha
6. Calculating HeI
7. Calculating NaI D1/D2

---

## Data Classes

### `ProcessingResult`

**New in v1.3.0** - Structured result object returned by `process_single_file()`.

**Fields:**
- `filename` (str): Input FITS filename
- `bjd` (float): Barycentric Julian Date
- `rv` (float): Radial velocity (km/s)
- `rv_error` (float): RV error (km/s)
- `bis` (float): Bisector span (km/s)
- `fwhm` (float): CCF FWHM (km/s)
- `contrast` (float): CCF contrast
- `s_index` (float): Ca II H&K S-index
- `s_index_error` (float): S-index error
- `halpha` (float): H-alpha index
- `halpha_error` (float): H-alpha error
- `hei` (float): He I index
- `hei_error` (float): He I error
- `nai_d1` (float): Na I D1 index
- `nai_d2` (float): Na I D2 index
- `spectrum_1d_path` (str or None): Path to saved 1D FITS spectrum (if `save=True`)
- `rest_frame_spectrum_path` (str or None): Path to rest-frame spectrum (reserved for future use)
- `processing_time` (dict): Dictionary mapping step names to execution time in seconds
- `errors` (str or None): Error message if processing failed

**Methods:**
- `to_dict()`: Convert to JSON-serializable dictionary

**Example:**
```python
result = cerespp.process_single_file('spectrum.fits', 'output/')

# Access fields
print(f"BJD: {result.bjd}")
print(f"S-index: {result.s_index}")

# Convert to dictionary for JSON serialization
data = result.to_dict()
import json
with open('result.json', 'w') as f:
    json.dump(data, f, indent=2)

# Check processing times
for step, duration in result.processing_time.items():
    print(f"{step}: {duration:.2f}s")
```

---

### `Spectrum1D`

**New in v1.3.0** - Metadata for 1D merged spectra.

**Fields:**
- `file_path` (str): Path to 1D spectrum FITS file
- `wavelengths_path` (str): Path to wavelength array (NPY file, reserved for future use)
- `fluxes_path` (str): Path to flux array (NPY file, reserved for future use)
- `errors_path` (str): Path to error array (NPY file, reserved for future use)
- `sn` (float): Signal-to-noise ratio
- `is_rest_frame` (bool): Whether spectrum is in rest frame
- `created_at` (datetime): Creation timestamp

**Methods:**
- `to_dict()`: Convert to JSON-serializable dictionary

---

## Classes

### `SpectrumProcessor`

**New in v1.3.0** - Core processor class for single-file processing.

**Constructor:**
```python
SpectrumProcessor(mask='G2', logger=None, progress_callback=None)
```

**Parameters:**
- `mask` (str, optional): Spectral mask. Default: `'G2'`
- `logger` (StructuredLogger, optional): Logger instance. Default: creates default logger
- `progress_callback` (callable, optional): Progress callback function. Default: `None`

**Methods:**

#### `process_file(filename, output_dir, save_1d=True)`

Process a single FITS file through all steps.

**Parameters:**
- `filename` (str): Path to FITS file
- `output_dir` (str): Output directory
- `save_1d` (bool, optional): Save 1D spectrum. Default: `True`

**Returns:**
- `ProcessingResult`: Structured results

**Example:**
```python
from cerespp.processor import SpectrumProcessor

processor = SpectrumProcessor(mask='K0')
result = processor.process_file('spectrum.fits', 'output/')
```

---

### `StructuredLogger`

**New in v1.3.0** - Logger with JSON-structured output.

**Constructor:**
```python
StructuredLogger(name, output_file=None)
```

**Parameters:**
- `name` (str): Logger name
- `output_file` (str, optional): Path to JSON log file. Default: `None` (console only)

**Methods:**

#### `log_step(step_name, status, **kwargs)`

Log a processing step.

**Parameters:**
- `step_name` (str): Name of the processing step
- `status` (str): Status (`'started'`, `'completed'`, `'failed'`)
- `**kwargs`: Additional key-value pairs to include in log entry

**Example:**
```python
from cerespp.logger import StructuredLogger

logger = StructuredLogger('my_processor', output_file='process.log')
logger.log_step('Loading FITS', 'started', filename='spectrum.fits')
# ... processing ...
logger.log_step('Loading FITS', 'completed', duration=0.5)
```

Each log entry is written as a JSON object with fields:
- `timestamp`: ISO 8601 timestamp
- `step`: Step name
- `status`: Status string
- Additional fields from `**kwargs`

#### `info(message, **kwargs)`, `warning(message, **kwargs)`, `error(message, **kwargs)`, `debug(message, **kwargs)`

Standard logging methods with JSON formatting.

---

## Progress Callback Signature

Progress callbacks receive the following arguments:

```python
def callback(step: str, **kwargs):
    """
    Args:
        step: Name of the current processing step
        **kwargs: Additional context (filename, duration, etc.)
    """
    pass
```

**Example Steps:**
- `"Loading FITS file"` - kwargs: `{'filename': str}`
- `"Converting to rest frame"` - kwargs may include `{'duration': float}`
- `"Merging echelle orders"` - kwargs: varies
- `"Calculating S-index"` - kwargs: varies
- `"Calculating H-alpha"` - kwargs: varies
- `"Calculating HeI"` - kwargs: varies
- `"Calculating NaI D1/D2"` - kwargs: varies

---

## Command-Line Interface

**New in v1.3.0** - CLI supports both single-file and bulk processing modes.

### Single-File Mode

```bash
cerespp --file spectrum.fits --output results/ --mask G2 --save-1d --verbose
```

**Arguments:**
- `--file`: Single FITS file to process
- `--output`: Output directory
- `--mask`: Spectral mask (G2, K0, K5, M2)
- `--save-1d`: Save 1D merged spectrum
- `--verbose`: Enable verbose logging

### Bulk Mode (Legacy)

```bash
cerespp --files spec1.fits spec2.fits spec3.fits --output results.dat --mask K0
```

**Arguments:**
- `--files`: List of FITS files to process
- `--output`: Output file path (`.dat`)
- `--mask`: Spectral mask

### Help

```bash
cerespp --help
```

---

## Legacy Functions

The following functions are available for backward compatibility:

- `ccf_gauss_plot()` - Plot CCF with Gaussian fit
- `ccf_plot()` - Plot CCF
- `line_plot()` - Plot activity line regions
- `ccf()` - Compute cross-correlation function
- `ccf_fit()` - Fit Gaussian to CCF
- `median_combine()` - Median combine spectra
- `merge_echelle()` - Merge echelle orders

See existing documentation and examples for usage details.

---

## Migration Guide

### Migrating from get_activities() to process_single_file()

**Before (v0.0.5):**
```python
files = glob.glob('*.fits')
activities, header = cerespp.get_activities(files, 'results.dat')
```

**After (v1.3.0):**
```python
files = glob.glob('*.fits')
results = []

for filename in files:
    result = cerespp.process_single_file(filename, 'results/')
    results.append(result)

# Access structured results
for result in results:
    print(f"{result.filename}: S-index = {result.s_index}")
```

**Note:** The old `get_activities()` function still works exactly as before. Migration is optional and recommended only if you need granular logging or structured results.
