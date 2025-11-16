#!/usr/bin/env python3
from backend.config import XTBConfig, get_logger
from backend.core.xtb_runner import XTBRunner

def main():
    cfg = XTBConfig()
    logger = get_logger(__name__)
    runner = XTBRunner(cfg, logger, enable_quality_logging=True)

    # Use a unique identifier for this test
    job_id = 'testjob_' + __import__('time').ctime().replace(' ', '_')

    # Use a simple molecule (SMILES, formula)
    molecule_smiles = 'O'
    molecule_formula = 'H2O'

    print('Logging molecule...')
    success, molecule_id = runner.log_molecule(molecule_smiles, molecule_formula, 'water_test_auto')
    if not success:
        # Maybe the molecule already exists (unique constraint). Try to find it.
        try:
            client = runner.supabase_client
            existing = client.get('molecules', filters={'smiles': molecule_smiles}, select='id')
            if existing:
                molecule_id = existing[0].get('id')
                success = True
                print('Found existing molecule id:', molecule_id)
        except Exception as e:
            print('Lookup for existing molecule failed:', e)
    print('Molecule logged:', success, molecule_id)

    if success and molecule_id:
        print('Logging calculation...')
        ok = runner.log_calculation(
            calc_id=job_id,
            molecule_id=molecule_id,
            energy=-5.07,
            homo=-7.5,
            lumo=-7.44407,
            gap=0.05593,
            dipole=1.0,
            total_charge=0,
            execution_time_seconds=12.5,
            xtb_version='6.7.1',
            convergence_status='converged',
            method='GFN2-xTB'
        )
        print('Calculation logged:', ok)
    else:
        print('Molecule logging failed; not logging calculation')


if __name__ == '__main__':
    main()
