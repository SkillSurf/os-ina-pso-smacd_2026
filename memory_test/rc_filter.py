import psutil
import os
import math
import ctypes
import numpy as np
import matplotlib.pyplot as plt

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import PySpice.Spice.NgSpice.Shared as Shared

dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(dir, "..", "pyspice", "ngspice-44_dll_64", "Spice64_dll", "dll-vs", "ngspice{}.dll")  # Ngspice 44
Shared.NgSpiceShared.LIBRARY_PATH = os.path.abspath(dll_path)

# Apply .format("") so it looks for "ngspice.dll" instead of "ngspice{}.dll"
exact_dll_path = Shared.NgSpiceShared.LIBRARY_PATH.format("")
ngspice_c_lib = ctypes.CDLL(exact_dll_path)  # Grab the raw C-library using ctypes

# =============================================================
# To handle latest ngspice versions that crash on 'run' command
# =============================================================
# Save PySpice's original command execution function
_original_exec_command = Shared.NgSpiceShared.exec_command

# Define a custom, forgiving wrapper
def _patched_exec_command(self, command, join_lines=True):
    try:
        return _original_exec_command(self, command, join_lines)
    except Shared.NgSpiceCommandError as e:
        # We silently pass and let PySpice continue retrieving the vectors!
        if command == 'run':
            pass 
        else:
            raise e  # If it's a real syntax error, crash normally

# Apply the patch globally
Shared.NgSpiceShared.exec_command = _patched_exec_command
# =============================================================

logger = Logging.setup_logging(logging_level='CRITICAL')

process = psutil.Process(os.getpid())
mem = {}

print("\nMemory Usage Test for PySpice with Ngspice C-API Reset...")
print("--------------------------------")

# Simulate multiple times
for i in range(1000):
    circuit = Circuit('Low-Pass RC Filter')

    circuit.V('vin', 'inp', circuit.gnd, 'DC 0.9 AC 1')
    R1 = circuit.R(1, 'inp', 'outp', 1@u_kΩ)
    C1 = circuit.C(1, 'outp', circuit.gnd, 1@u_uF)

    break_frequency = 1 / (2 * math.pi * float(R1.resistance * C1.capacitance))

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)

    try:
        analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_MHz, number_of_points=10,  variation='dec')

    finally:
        # Hit the Ngspice C-API Reset Button directly
        ngspice_c_lib.ngSpice_Reset()

        # Re-initialize PySpice
        ngspice = simulator.factory(circuit).ngspice

        if ngspice:
            # FIX: Force the internal ID back to a standard Python integer (0)
            # so CFFI doesn't choke trying to parse an existing pointer.
            ngspice._ngspice_id = 0 
            ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine!

    # Memory Tracking
    mem_after = process.memory_info().rss / (1024 ** 2)
    if i == 0:
        mem['initial'] = mem_after
        print(f"Initial Memory Usage: {mem_after:.2f} MB")

    if (i+1) % 100 == 0:
        print(f"Iteration {i+1} | Mem: {mem_after:.2f} MB")

if 'initial' in mem:
    mem['final'] = mem_after
    print("--------------------------------")
    print(f"Change in Memory Usage: {mem['final'] - mem['initial']:.2f} MB")

# # Plotting the Bode diagram
# fig, ax = plt.subplots(figsize=(10, 6))
# ax.semilogx(analysis.frequency, 20 * np.log10(np.absolute(analysis.nodes['outp'] / analysis.nodes['inp'])), label='Magnitude (dB)')
# ax.set_title('Bode Diagram of Low-Pass RC Filter')
# ax.set_xlabel('Frequency (Hz)')
# ax.set_ylabel('Magnitude (dB)')
# ax.grid(which='both', linestyle='--', linewidth=0.5)
# ax.axvline(break_frequency, color='red', linestyle='--', label='Break Frequency')
# ax.legend()

# plt.tight_layout()
# plt.show()

print("\nMemory Usage Test for PySpice with Ngspice on normal 'run' command...")
print("--------------------------------")

 # Simulate multiple times
for i in range(1000):
    circuit = Circuit('Low-Pass RC Filter')

    circuit.V('vin', 'inp', circuit.gnd, 'DC 0.9 AC 1')
    R1 = circuit.R(1, 'inp', 'outp', 1@u_kΩ)
    C1 = circuit.C(1, 'outp', circuit.gnd, 1@u_uF)

    break_frequency = 1 / (2 * math.pi * float(R1.resistance * C1.capacitance))

    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=1@u_MHz, number_of_points=10,  variation='dec')

    mem_before = process.memory_info().rss / (1024 ** 2)

    # ngspice = simulator.factory(circuit).ngspice
    # ngspice.remove_circuit()  # I find this is necessary!!!
    # ngspice.destroy()  # this might not be needed 

    mem_after = process.memory_info().rss / (1024 ** 2)
    if i == 0:
        mem['initial'] = mem_after
        print(f"Initial Memory Usage: {mem_after:.2f} MB")

    if (i+1) % 100 == 0:  # Print memory usage every 100 iterations
        print(f"Iteration {i+1} | Mem: {mem_after:.2f} MB")

if 'initial' in mem:
    mem['final'] = mem_after
    print("--------------------------------")
    print(f"Change in Memory Usage: {mem['final'] - mem['initial']:.2f} MB")