"""
Strategy pattern implementation for Quantum Forge Worker.

Defines an extensible architecture for executing diverse computational chemistry jobs.
Each "Strategy" encapsulates the logic for a specific backend (xtb, ORCA, Gaussian, etc.).

Key design:
- ComputationalStrategy: Abstract base class defining the contract.
- JobContext: Data class holding shared resources (DB cursor, logger, parameters).
- XTBStrategy: Concrete implementation for Extended Tight Binding calculations.
- StrategyFactory: Simple mechanism to instantiate the correct strategy.

This design allows the worker to remain agnostic to the underlying chemistry engine,
enabling future expansion without modifying core worker logic.
"""

import subprocess
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import tempfile
import os

logger = logging.getLogger(__name__)


@dataclass
class JobContext:
    """
    Holds shared resources for strategy execution.
    
    This context is passed to every strategy's execute() method, providing
    access to the database, logger, and job parameters.
    """
    job_id: str
    user_id: str
    parameters: Dict[str, Any]
    working_dir: str
    timeout: int


class ComputationalStrategy(ABC):
    """
    Abstract base class defining the interface for computational strategies.
    
    Every strategy must implement the execute() method, which runs the
    computation and returns a result dictionary.
    """
    
    @abstractmethod
    def execute(self, context: JobContext) -> Dict[str, Any]:
        """
        Execute the computational task.
        
        Args:
            context: JobContext instance with job details and resources.
        
        Returns:
            Dictionary containing results, metadata, and execution info:
            {
                'status': 'success' | 'failure',
                'output': <binary or string output>,
                'exit_code': <int>,
                'stdout': <str>,
                'stderr': <str>,
                'execution_time': <float>,
                'message': <str>,
            }
        
        Raises:
            Exception: If the strategy encounters a fatal error.
                Callers should catch and log the exception, marking the job as failed.
        """
        pass


class XTBStrategy(ComputationalStrategy):
    """
    Concrete strategy for Extended Tight Binding (xtb) calculations.
    
    xtb is a fast, open-source semi-empirical quantum chemistry code.
    Reference: https://github.com/grimme-lab/xtb
    
    This implementation:
    - Accepts input parameters (e.g., input file path, calculation type).
    - Invokes the xtb binary via subprocess.run.
    - Captures stdout, stderr, and exit code.
    - Enforces a timeout to prevent hanging jobs.
    - Returns structured output for the worker to persist.
    """
    
    def execute(self, context: JobContext) -> Dict[str, Any]:
        """
        Execute an xtb quantum chemistry job.
        
        Expected parameters in context.parameters:
        {
            'input_file': 'path/to/input.xyz',  # Required: molecular structure
            'calculation_type': 'opt' | 'sp' | 'md',  # Required: optimization, single point, or molecular dynamics
            'additional_args': [...],  # Optional: extra xtb command-line arguments
            'num_threads': 4,  # Optional: number of OMP threads
        }
        """
        logger.info(f"XTBStrategy.execute() starting for job {context.job_id}")
        
        try:
            # Extract parameters with defaults
            input_file = context.parameters.get('input_file')
            calc_type = context.parameters.get('calculation_type', 'sp')
            additional_args = context.parameters.get('additional_args', [])
            num_threads = context.parameters.get('num_threads', 4)
            
            if not input_file:
                return {
                    'status': 'failure',
                    'exit_code': -1,
                    'message': 'Missing required parameter: input_file',
                    'stdout': '',
                    'stderr': '',
                    'execution_time': 0.0,
                }
            
            # Construct the xtb command
            cmd = ['xtb']
            
            # Add the input file
            cmd.append(input_file)
            
            # Add the calculation type (e.g., --opt, --sp, --md)
            if calc_type in ['opt', 'sp', 'md']:
                cmd.append(f'--{calc_type}')
            else:
                logger.warning(f"Unknown calculation_type '{calc_type}'; defaulting to --sp")
                cmd.append('--sp')
            
            # Add any additional arguments
            if isinstance(additional_args, list):
                cmd.extend(additional_args)
            
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Prepare environment: set OMP_NUM_THREADS for parallelism
            env = os.environ.copy()
            env['OMP_NUM_THREADS'] = str(num_threads)
            
            # Run the xtb command with timeout
            import time
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    cmd,
                    cwd=context.working_dir,
                    capture_output=True,
                    text=True,
                    timeout=context.timeout,
                    env=env,
                )
                execution_time = time.time() - start_time
                
                logger.info(f"xtb completed with exit code {result.returncode} in {execution_time:.2f}s")
                
                return {
                    'status': 'success' if result.returncode == 0 else 'failure',
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'execution_time': execution_time,
                    'message': f'xtb exited with code {result.returncode}',
                }
            
            except subprocess.TimeoutExpired as e:
                execution_time = time.time() - start_time
                logger.error(f"xtb timed out after {context.timeout} seconds")
                return {
                    'status': 'failure',
                    'exit_code': -1,
                    'stdout': e.stdout or '',
                    'stderr': e.stderr or 'Process timed out',
                    'execution_time': execution_time,
                    'message': f'Job timed out after {context.timeout} seconds',
                }
        
        except Exception as e:
            logger.exception(f"XTBStrategy.execute() raised an exception: {e}")
            return {
                'status': 'failure',
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time': 0.0,
                'message': f'Strategy execution failed: {type(e).__name__}: {e}',
            }


class DummyStrategy(ComputationalStrategy):
    """
    A dummy/mock strategy for testing the worker without running actual xtb.
    
    Useful for development, testing, and debugging. Simply echoes parameters
    and returns a successful result.
    """
    
    def execute(self, context: JobContext) -> Dict[str, Any]:
        """
        Execute a dummy job that simulates successful execution.
        """
        logger.info(f"DummyStrategy.execute() called for job {context.job_id}")
        logger.debug(f"Parameters: {context.parameters}")
        
        import time
        start_time = time.time()
        time.sleep(1)  # Simulate some work
        execution_time = time.time() - start_time
        
        return {
            'status': 'success',
            'exit_code': 0,
            'stdout': f"Dummy job {context.job_id} completed successfully\n",
            'stderr': '',
            'execution_time': execution_time,
            'message': 'Dummy strategy executed successfully',
        }


class StrategyFactory:
    """
    Factory for instantiating the correct computational strategy.
    
    Usage:
        strategy = StrategyFactory.create('xtb')
        result = strategy.execute(context)
    """
    
    _strategies = {
        'xtb': XTBStrategy,
        'dummy': DummyStrategy,
    }
    
    @classmethod
    def register(cls, name: str, strategy_class: type) -> None:
        """Register a new strategy."""
        if not issubclass(strategy_class, ComputationalStrategy):
            raise TypeError(f"{strategy_class} must inherit from ComputationalStrategy")
        cls._strategies[name] = strategy_class
        logger.info(f"Registered strategy '{name}': {strategy_class.__name__}")
    
    @classmethod
    def create(cls, strategy_name: str) -> ComputationalStrategy:
        """
        Create an instance of the specified strategy.
        
        Args:
            strategy_name: Name of the strategy (e.g., 'xtb', 'dummy').
        
        Returns:
            Instantiated strategy object.
        
        Raises:
            ValueError: If the strategy name is not registered.
        """
        if strategy_name not in cls._strategies:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(
                f"Unknown strategy '{strategy_name}'. "
                f"Available strategies: {available}"
            )
        
        strategy_class = cls._strategies[strategy_name]
        return strategy_class()
    
    @classmethod
    def list_strategies(cls) -> list[str]:
        """Return a list of available strategy names."""
        return list(cls._strategies.keys())
