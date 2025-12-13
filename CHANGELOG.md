# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-12-13

### Added
- Single-file processing API with `process_single_file()` function
- Structured result dataclass `ProcessingResult` with JSON serialization support
- Progress callback support for real-time monitoring of processing steps
- Structured logging with `StructuredLogger` class for JSON-formatted logs
- CLI support for single-file mode with `--file` flag
- Per-step timing information in processing results
- `Spectrum1D` dataclass for tracking 1D spectrum metadata
- `SpectrumProcessor` class for modular, step-by-step processing

### Changed
- Refactored `get_activities()` to use `SpectrumProcessor` internally
- Improved error handling - batch processing continues on individual file failures
- Updated scipy compatibility for `trapz` (now `trapezoid`) and `triang` (moved to `scipy.signal.windows`)
- Replaced deprecated `pkg_resources` with `importlib.metadata` for version retrieval

### Fixed
- Compatibility with modern scipy versions (>= 1.10.0)
- Deprecation warnings from pkg_resources

## [0.0.5] - Previous Release

Initial public release with core functionality.
