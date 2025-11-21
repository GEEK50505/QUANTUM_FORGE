#!/usr/bin/env python3
"""
Standalone script to run a single xTB job with full logging.
"""
import argparse
import sys
import os

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core.logger import setup_logger
from backend.core.compat import XTBRunner


def main():
    """Main entry point for the xTB job runner."""
    parser = argparse.ArgumentParser(description="QUANTUM_FORGE xTB Job Runner")
    parser.add_argument("input_xyz", help="Input XYZ file path")
    parser.add_argument("--workdir", default="./runs", help="Working directory")
    parser.add_argument("--level", choices=["tight", "normal", "crude"], 
                       default="tight", help="Optimization level")
    parser.add_argument("--output-dir", default="./results", help="Output directory")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("run_job")
    logger.info("QUANTUM_FORGE xTB Job Runner")
    logger.info(f"Input: {args.input_xyz}")
    logger.info(f"Method: {args.level} optimization")
    logger.info(f"Working directory: {args.workdir}")
    logger.info(f"Output directory: {args.output_dir}")
    
    try:
        # Create runner
        runner = XTBRunner(args.input_xyz, args.workdir, logger)
        
        # Run job
        results = runner.run(optimization_level=args.level)
        
        # Check if job was successful
        if not results["success"]:
            logger.error(f"Job failed: {results['error']}")
            return 1
        
        # Parse results if we have output
        parsed_results = results.get("results", {})
        if parsed_results:
            logger.info("Successfully parsed results")
        else:
            logger.warning("No results to parse")
        
        # Save results and metadata
        results_file = runner.save_results(results, args.output_dir)
        metadata_file = runner.save_metadata(results, args.output_dir)
        
        # Log final summary
        convergence_status = parsed_results.get("convergence_status", "UNKNOWN")
        logger.info(f"Job completed successfully with {convergence_status}")
        
        # Log results summary
        total_energy = parsed_results.get("total_energy", "N/A")
        homo_lumo_gap = parsed_results.get("homo_lumo_gap", "N/A")
        converged = "yes" if convergence_status == "CONVERGED" else "no"
        logger.info(f"Energy: {total_energy} Ha, Gap: {homo_lumo_gap} eV, Converged: {converged}")
        
        logger.info(f"Results saved to {results_file}")
        logger.info(f"Metadata saved to {metadata_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())