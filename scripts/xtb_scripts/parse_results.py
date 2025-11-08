#!/usr/bin/env python3
"""
Standalone parser script to extract data from existing logs.
"""
import argparse
import csv
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core.logger import setup_logger
from backend.simulation.classical_sim.xtb_parser import XTBLogParser


def main():
    """Main entry point for the results parser."""
    parser = argparse.ArgumentParser(description="Parse xTB results from log files")
    parser.add_argument("--log-file", help="Single log file to parse")
    parser.add_argument("--log-dir", help="Directory containing log files")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("parse_results")
    logger.info("Parsing xTB results")
    
    # Determine files to process
    log_files = []
    
    if args.log_file:
        log_file = Path(args.log_file)
        if log_file.exists():
            log_files = [log_file]
        else:
            logger.error(f"Log file does not exist: {log_file}")
            return 1
    elif args.log_dir:
        log_dir = Path(args.log_dir)
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            logger.info(f"Found {len(log_files)} log files in {log_dir}")
        else:
            logger.error(f"Log directory does not exist: {log_dir}")
            return 1
    else:
        logger.error("Either --log-file or --log-dir must be specified")
        return 1
    
    if not log_files:
        logger.warning("No log files to process")
        return 0
    
    # Process each log file
    summary_data = []
    
    for log_file in log_files:
        logger.info(f"Processing: {log_file}")
        
        try:
            # Create parser
            parser = XTBLogParser(str(log_file), logger)
            
            # Extract all data
            results = parser.parse_all()
            
            # Log extracted values
            total_energy = results.get("total_energy", "N/A")
            homo_lumo_gap = results.get("homo_lumo_gap", "N/A")
            convergence_status = results.get("convergence_status", "UNKNOWN")
            logger.info(f"Energy: {total_energy}, Gap: {homo_lumo_gap}, Status: {convergence_status}")
            
            # Add to summary
            summary_data.append({
                "filename": log_file.name,
                "energy": total_energy,
                "gap": homo_lumo_gap,
                "converged": convergence_status,
                "timestamp": results.get("line_count", "N/A")
            })
            
        except Exception as e:
            logger.error(f"Failed to parse {log_file}: {e}")
            continue
    
    # Create summary CSV
    if summary_data:
        output_file = "results_summary.csv"
        try:
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ['filename', 'energy', 'gap', 'converged', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(summary_data)
            
            logger.info(f"Summary saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save summary CSV: {e}")
            return 1
    else:
        logger.warning("No data to summarize")
    
    return 0


if __name__ == "__main__":
    exit(main())