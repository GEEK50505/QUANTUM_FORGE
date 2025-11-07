#!/usr/bin/env python3
"""
Automated batch job runner for multiple molecules.
"""
import argparse
import json
import time
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core.logger import setup_logger
from backend.simulation.classical_sim.xtb_runner import XTBRunner


def main():
    """Main entry point for the batch job runner."""
    parser = argparse.ArgumentParser(description="QUANTUM_FORGE Batch Job Runner")
    parser.add_argument("--input-dir", required=True, help="Input directory with XYZ files")
    parser.add_argument("--output-dir", default="./results", help="Output directory")
    parser.add_argument("--level", choices=["tight", "normal", "crude"], 
                       default="tight", help="Optimization level")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("batch_run")
    logger.info("Starting batch job runner")
    
    # Find XYZ files
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
    
    xyz_files = list(input_dir.glob("*.xyz"))
    logger.info(f"Found {len(xyz_files)} molecules in {input_dir}")
    
    if not xyz_files:
        logger.warning("No XYZ files found in input directory")
        return 0
    
    # Track results
    batch_report = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_dir": str(input_dir),
        "output_dir": args.output_dir,
        "optimization_level": args.level,
        "jobs": []
    }
    
    success_count = 0
    failure_count = 0
    failed_molecules = []
    
    # Process each molecule
    start_time = time.time()
    
    for xyz_file in xyz_files:
        molecule_name = xyz_file.stem
        logger.info(f"Processing: {molecule_name}")
        
        job_start_time = time.time()
        
        try:
            # Create runner
            runner = XTBRunner(str(xyz_file), "./runs", logger)
            
            # Run job
            results = runner.run(optimization_level=args.level)
            
            # Save results
            if results["success"]:
                runner.save_results(results, args.output_dir)
                runner.save_metadata(results, args.output_dir)
                success_count += 1
                logger.info(f"Completed: {molecule_name} successfully")
            else:
                failure_count += 1
                failed_molecules.append({
                    "molecule": molecule_name,
                    "error": results["error"]
                })
                logger.error(f"Failed: {molecule_name} - {results['error']}")
            
            # Record job info
            job_time = time.time() - job_start_time
            batch_report["jobs"].append({
                "molecule": molecule_name,
                "job_id": results.get("job_id", "unknown"),
                "success": results["success"],
                "error": results["error"],
                "time_seconds": round(job_time, 2)
            })
            
            logger.info(f"Completed: {molecule_name} in {job_time:.2f} seconds")
            
        except Exception as e:
            failure_count += 1
            failed_molecules.append({
                "molecule": molecule_name,
                "error": str(e)
            })
            logger.error(f"Exception processing {molecule_name}: {e}")
            continue
    
    # Calculate total execution time
    total_time = time.time() - start_time
    
    # Log final summary
    logger.info(f"Batch completed: {success_count} succeeded, {failure_count} failed")
    logger.info(f"Total execution time: {total_time:.2f} seconds")
    
    # Log failed molecules if any
    if failed_molecules:
        logger.error("Failed molecules:")
        for failed in failed_molecules:
            logger.error(f"  {failed['molecule']}: {failed['error']}")
    
    # Save batch report
    batch_report["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    batch_report["total_time_seconds"] = round(total_time, 2)
    batch_report["success_count"] = success_count
    batch_report["failure_count"] = failure_count
    batch_report["failed_molecules"] = failed_molecules
    
    report_file = Path(args.output_dir) / "batch_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(report_file, 'w') as f:
            json.dump(batch_report, f, indent=2)
        logger.info(f"Batch report saved to {report_file}")
    except Exception as e:
        logger.error(f"Failed to save batch report: {e}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    exit(main())