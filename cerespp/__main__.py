"""Command-line interface for Ceres++.

Provides both legacy bulk processing mode and new single-file mode
for backward compatibility.

Author: Jose Vines
"""
import argparse
import sys
from .cerespp import get_activities, process_single_file
from .logger import StructuredLogger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Ceres++ Activity Analysis for Stellar Spectra',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # New: Process single file with verbose logging
  cerespp --file spectrum.fits --output out/ --save-1d --verbose

  # Legacy: Bulk processing
  cerespp --files spectrum1.fits spectrum2.fits --output results.dat --mask G2
        """
    )

    # File input options
    file_group = parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument(
        '--file',
        help='Single FITS file to process (new mode)'
    )
    file_group.add_argument(
        '--files',
        nargs='+',
        help='List of FITS files to process (legacy mode)'
    )

    # Output options
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for results'
    )

    # Processing options
    parser.add_argument(
        '--mask',
        default='G2',
        choices=['G2', 'K0', 'K5', 'M2'],
        help='Mask for RV calculation (default: G2)'
    )

    parser.add_argument(
        '--save-1d',
        action='store_true',
        help='Save merged 1D spectra to FITS files'
    )

    # Logging options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--log-file',
        help='Write JSON-structured logs to file'
    )

    args = parser.parse_args()

    # Configure logger
    logger = None
    if args.verbose or args.log_file:
        import logging
        level = logging.DEBUG if args.verbose else logging.INFO
        logger = StructuredLogger(
            'cerespp.cli',
            output_file=args.log_file,
            level=level
        )

    # Process files
    if args.file:
        # New single-file mode
        logger.info(f"Processing single file: {args.file}") if logger else None

        result = process_single_file(
            args.file,
            args.output,
            mask=args.mask,
            save=args.save_1d,
            logger=logger
        )

        if result.errors:
            print(f"Error: {result.errors}", file=sys.stderr)
            sys.exit(1)

        # Print results
        print(f"Processed: {args.file}")
        print(f"BJD: {result.bjd:.6f}")
        if result.s_index != -999:
            print(f"S-index: {result.s_index:.3f} ± {result.s_index_error:.3f}")
        print(f"H-alpha: {result.halpha:.3f} ± {result.halpha_error:.3f}")
        print(f"HeI: {result.hei:.3f} ± {result.hei_error:.3f}")
        print(f"NaI D1+D2: {result.nai_d1d2:.3f} ± {result.nai_d1d2_error:.3f}")
        if result.fwhm is not None:
            print(f"FWHM: {result.fwhm:.3f} ± {result.fwhm_error:.3f}")
        print(f"BIS: {result.bis:.3f} ± {result.bis_error:.3f}")
        print(f"Contrast: {result.contrast:.3f}")

        if result.spectrum_1d_path:
            print(f"1D spectrum saved to: {result.spectrum_1d_path}")

        if args.verbose and result.processing_time:
            print("\nProcessing times:")
            for step, duration in result.processing_time.items():
                print(f"  {step}: {duration:.2f}s")

    elif args.files:
        # Legacy bulk mode
        logger.info(f"Processing {len(args.files)} files") if logger else None

        data, header = get_activities(
            args.files,
            args.output,
            mask=args.mask,
            save=args.save_1d,
            logger=logger
        )

        print(f"Processed {len(args.files)} files")
        print(f"Results saved to: {args.output}/")

    else:
        parser.error("Must provide --file or --files")


if __name__ == '__main__':
    main()
