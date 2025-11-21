import abc
import os
import json
import subprocess
import threading
import tempfile
import re
from typing import Dict, Any, Optional, Callable


class ComputeStrategy(abc.ABC):
    @abc.abstractmethod
    def run(self, payload: Dict[str, Any], workdir: str, log_writer: Callable[[bytes], None]) -> Dict[str, Any]:
        """Execute the compute job.

        - payload: job payload from DB
        - workdir: path to a temporary working directory
        - log_writer: function to append bytes to a log file/stream

        Returns a result dict (JSON-serializable) with at least energy_scf and homo_lumo_gap keys when available.
        """
        raise NotImplementedError()


class XTBStrategy(ComputeStrategy):
    """Runs xTB on provided coordinates.

    Expects payload like: {"method": "gfn2", "coords": "...xyz text..."}
    """

    def __init__(self, xtb_binary: str = 'xtb'):
        self.xtb_binary = xtb_binary

    def run(self, payload: Dict[str, Any], workdir: str, log_writer: Callable[[bytes], None]) -> Dict[str, Any]:
        coords = payload.get('coords') or payload.get('geometry') or payload.get('coords_xyz')
        method = payload.get('method', 'gfn2')
        if not coords:
            raise ValueError('No coordinates provided in payload')

        # write geometry to file
        inp_path = os.path.join(workdir, 'molecule.xyz')
        with open(inp_path, 'w', encoding='utf-8') as f:
            f.write(coords)

        # Build xtb command (example). Users may tweak flags as needed.
        cmd = [self.xtb_binary, inp_path, '--gfn', method]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Stream stdout and capture content
        stdout_chunks = []
        assert proc.stdout is not None
        while True:
            chunk = proc.stdout.readline()
            if not chunk:
                break
            try:
                log_writer(chunk)
            except Exception:
                pass
            stdout_chunks.append(chunk.decode('utf-8', errors='replace'))

        proc.wait()
        output = ''.join(stdout_chunks)

        # Parse output for energy and homo/lumo
        energy = self._parse_energy(output)
        homo_lumo = self._parse_homo_lumo(output)

        result = {
            'energy_scf': energy,
            'homo_lumo_gap': homo_lumo,
            'raw_output': output,
        }
        return result

    def _parse_energy(self, txt: str) -> Optional[float]:
        # Try several common patterns
        patterns = [r'TOTAL ENERGY\s*=\s*([\-0-9\.Ee]+)', r'TOTAL SCF ENERGY\s*=\s*([\-0-9\.Ee]+)', r'ENERGY\s*:\s*([\-0-9\.Ee]+)']
        for p in patterns:
            m = re.search(p, txt, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except Exception:
                    continue
        # fallback: look for a lone number near 'energy'
        m = re.search(r'energy[^\n\r0-9\-]*([\-0-9\.Ee]+)', txt, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                return None
        return None

    def _parse_homo_lumo(self, txt: str) -> Optional[float]:
        # Try to parse HOMO and LUMO and compute gap
        m_h = re.search(r'HOMO[^\n]*?([\-0-9\.Ee]+)', txt, re.IGNORECASE)
        m_l = re.search(r'LUMO[^\n]*?([\-0-9\.Ee]+)', txt, re.IGNORECASE)
        try:
            if m_h and m_l:
                h = float(m_h.group(1))
                l = float(m_l.group(1))
                return l - h
        except Exception:
            return None
        return None
