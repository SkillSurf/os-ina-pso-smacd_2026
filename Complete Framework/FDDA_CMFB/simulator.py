import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter

from specs import *
from gmID_sizing import get_Area

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_V, u_pF, u_GH, u_GF, u_Hz, u_MHz, u_ns, u_us
import PySpice.Spice.NgSpice.Shared as Shared

dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(dir, "..", "..", "pyspice", "ngspice-44_dll_64", "Spice64_dll", "dll-vs", "ngspice{}.dll")  # Ngspice 44
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

# ============================================================
# Generates a hard-coded SPICE file in OPEN-LOOP configuration
# ============================================================
def generate_spice(params):

    # Read the SPICE template file
    with open('ref.spice', 'r') as f:
        template = f.read()

    # Inject the parameters into the placeholders in the SPICE template
    spice = template.format(
    # Extract parameters
    W_1 = params['W_1'], L_1 = params['L_1'],
    W_2 = params['W_2'], L_2 = params['L_2'],
    W_3 = params['W_3'], L_3 = params['L_3'],
    W_4 = params['W_4'], L_4 = params['L_4'],
    W_5 = params['W_5'], L_5 = params['L_5'],
    W_6 = params['W_6'], L_6 = params['L_6'],
    W_7 = params['W_7'], L_7 = params['L_7'],
    W_8 = params['W_8'], L_8 = params['L_8'],
    V_B1 = params['V_B1'],
    V_B2 = params['V_B2'],
    V_B3 = params['V_B3'],
    V_B4 = params['V_B4'],
    V_CM = params['V_CM'],
    Template = 'Auto-Generated'
    )
    
    with open('fdda_cmfb.spice', 'w') as f:
        f.write(spice)

# ======================
# Runs the AC simulation
# ======================
def runsim_AC(measurement_results, plots=False, log_dir=None):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include fdda_cmfb.spice
"""
    circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.V('VDD', 'VDD', circuit.gnd, 1.8@u_V)

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Series feedback with infinite inductor and parallel feedback with infinite capacitor (to ensure proper DC biasing)
    circuit.L('LFB1', 'V_PN', 'V_OP', 4@u_GH)
    circuit.L('LFB2', 'V_NN', 'V_ON', 4@u_GH)
    circuit.C('CFB1', 'V_PN', circuit.gnd, 4@u_GF)
    circuit.C('CFB2', 'V_NN', circuit.gnd, 4@u_GF)

    # Define AC Input (Differential)
    circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9 AC 1')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC -1')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
    except Exception as e:
        raise e
    
    freq = np.array(analysis.frequency)
    vout = analysis.nodes['v_op'] - analysis.nodes['v_on']
    vin  = (analysis.nodes['v_pp'] - analysis.nodes['v_pn']) - (analysis.nodes['v_np'] - analysis.nodes['v_nn'])

    gain = vout / vin
    gain_db = 20 * np.log10(np.abs(gain))
    phase_deg = np.angle(gain, deg=True)

    dc_gain = gain_db[0]
    gbw = np.interp(0, gain_db[::-1], freq[::-1])
    phase_at_gbw = np.interp(gbw, freq, phase_deg)
    phase_margin = 180 + phase_at_gbw

    measurement_results['Gain_dB'] = float(dc_gain)
    measurement_results['GBW'] = float(gbw)
    measurement_results['PM'] = float(phase_margin)

    if plots and log_dir is not None:
        _, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.semilogx(freq, gain_db, color='blue', linestyle='-')
        ax1.set_ylabel('Gain (dB)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("Bode Plot of FDDA-CMFB")

        ax2.semilogx(freq, phase_deg, color='blue', linestyle='-')
        ax2.set_ylabel('Phase (Degrees)')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.grid(True, which="both", ls="-")
        ticks = [0.1, 1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
        labels = ['0.1', '1', '10', '100', '1K', '10K', '100K', '1M', '10M', '100M']
        ax2.xaxis.set_major_locator(FixedLocator(ticks))
        ax2.xaxis.set_major_formatter(FixedFormatter(labels))

        ax1.axhline(y=0, color='red', linestyle='--') 
        ax2.axhline(y=-180, color='red', linestyle='--') 

        plt.savefig(os.path.join(log_dir, 'Gain_and_GBW_plot.png'))
        plt.tight_layout()

    # Hit the Ngspice C-API Reset Button directly
    ngspice_c_lib.ngSpice_Reset()  
    ngspice = simulator.factory(circuit).ngspice  # Re-initialize PySpice
    if ngspice:
        # FIX: Force the internal ID back to a standard Python integer (0)
        # so CFFI doesn't choke trying to parse an existing pointer.
        ngspice._ngspice_id = 0 
        ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine

    return gain_db

# ======================
# Runs the OP simulation
# ======================
def runsim_OP(measurement_results, plots=False, log_dir=None):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include fdda_cmfb.spice
"""
    circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.V('VDD', 'VDD', circuit.gnd, 1.8@u_V)

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Series feedback with infinite inductor and parallel feedback with infinite capacitor (to ensure proper DC biasing)
    circuit.L('LFB1', 'V_PN', 'V_OP', 4@u_GH)
    circuit.L('LFB2', 'V_NN', 'V_ON', 4@u_GH)
    circuit.C('CFB1', 'V_PN', circuit.gnd, 4@u_GF)
    circuit.C('CFB2', 'V_NN', circuit.gnd, 4@u_GF)

    # Define DC Inputs (Quiescent Points)
    circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)
    simulator.save_currents = True

    try:
        analysis = simulator.operating_point()
    except Exception as e:
        raise e
    
    iq = float(analysis.branches['vvdd'][0])
    power = abs(iq) * VDD
    v_cmfb = float(analysis.nodes['v_cmfb'][0])

    measurement_results['Power'] = power
    measurement_results['V_CMFB'] = v_cmfb

    if plots and log_dir is not None:
        # Write all operating point values to a text file
        with open(os.path.join(log_dir, 'op_results.txt'), 'w') as f:
            f.write("Operating Point Analysis Results:\n")
            f.write(f"Quiescent Current (I_Q): {abs(iq)*1e6:.2f} uA\n")
            f.write(f"Power Consumption: {power*1e6:.2f} uW\n")
            f.write("\nDetailed Node Voltages:\n")
            for node in analysis.nodes:
                voltage = float(analysis.nodes[node][0])
                f.write(f"{node}: {voltage:.5f} V\n")
            f.write("\nDetailed Branch Currents:\n")
            for branch in analysis.branches:
                current = float(analysis.branches[branch][0])
                f.write(f"{branch}: {current*1e6:.2f} uA\n")
            f.write("\nInternal Parameters:\n")
            for key in analysis.internal_parameters:
                if len(analysis[key]) > 0:
                    current = float(analysis[key].item())
                    f.write(f"{key}: {current*1e6:.2f} uA\n")

    # Hit the Ngspice C-API Reset Button directly
    ngspice_c_lib.ngSpice_Reset()  
    ngspice = simulator.factory(circuit).ngspice  # Re-initialize PySpice
    if ngspice:
        # FIX: Force the internal ID back to a standard Python integer (0)
        # so CFFI doesn't choke trying to parse an existing pointer.
        ngspice._ngspice_id = 0 
        ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine

# ========================
# Runs the SLEW simulation
# ========================
def runsim_SLEW(measurement_results, plots=False, log_dir=None):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include fdda_cmfb.spice
"""
    # Form the closed-loop configuration (Unity gain)
    circuit.X('X1', 'FDDA', 'V_PP', 'V_OP', 'V_NP', 'V_ON', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.V('VDD', 'VDD', circuit.gnd, 1.8@u_V)

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Define Pulse Inputs (Differential)
    circuit.V('VPP', 'V_PP', circuit.gnd, 'PULSE(0 1.8 10u 10p 10p 20u 40u)')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'PULSE(1.8 0 10u 10p 10p 20u 40u)')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.transient(step_time=10@u_ns, end_time=20@u_us)
    except Exception as e:
        raise e
    
    time = np.array(analysis.time)
    vin = analysis.nodes['v_pp'] - analysis.nodes['v_np']
    vout = analysis.nodes['v_op'] - analysis.nodes['v_on']
    
    v_min = np.interp(1e-6, time, vout)   # Voltage at 1μs
    v_max = np.interp(19e-6, time, vout)  # Voltage at 19μs

    v_swing = float(v_max) - float(v_min)
    v_10 = float(v_min) + (0.1 * v_swing)
    v_90 = float(v_max) - (0.1 * v_swing)

    t_10 = np.interp(v_10, vout, time)
    t_90 = np.interp(v_90, vout, time)

    slew = (v_90 - v_10) / (t_90 - t_10)

    measurement_results['SR'] = float(slew)

    if plots and log_dir is not None:
        _, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.plot(time*1e6, vin, color='blue', linestyle='-')
        ax1.set_ylabel('Input Voltage (V)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("FDDA-CMFB Slew Response")

        ax2.plot(time*1e6, vout, color='blue', linestyle='-')
        ax2.set_ylabel('Output Voltage (V)')
        ax2.set_xlabel('Time (μs)')
        ax2.grid(True, which="both", ls="-")

        if slew > 0:
            ax2.scatter([t_10*1e6, t_90*1e6], [v_10, v_90], color='black', zorder=5)

        plt.savefig(os.path.join(log_dir, 'Slew_plot.png'))
        plt.tight_layout()

    # Hit the Ngspice C-API Reset Button directly
    ngspice_c_lib.ngSpice_Reset()  
    ngspice = simulator.factory(circuit).ngspice  # Re-initialize PySpice
    if ngspice:
        # FIX: Force the internal ID back to a standard Python integer (0)
        # so CFFI doesn't choke trying to parse an existing pointer.
        ngspice._ngspice_id = 0 
        ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine

# ========================
# Runs the CMRR simulation
# ========================
def runsim_CMRR(gain_dm_db, measurement_results, plots=False, log_dir=None):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include fdda_cmfb.spice
"""
    circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.V('VDD', 'VDD', circuit.gnd, 1.8@u_V)

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Series feedback with infinite inductor and parallel feedback with infinite capacitor (to ensure proper DC biasing)
    circuit.L('LFB1', 'V_PN', 'V_OP', 4@u_GH)
    circuit.L('LFB2', 'V_NN', 'V_ON', 4@u_GH)
    circuit.C('CFB1', 'V_PN', circuit.gnd, 4@u_GF)
    circuit.C('CFB2', 'V_NN', circuit.gnd, 4@u_GF)

    # Define AC Input (Common Mode)
    circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9 AC 1')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC 1')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
    except Exception as e:
        raise e
    
    freq = np.array(analysis.frequency)
    vout_cm = analysis.nodes['v_op'] - analysis.nodes['v_on']
    vin_cm  = (analysis.nodes['v_pp'] + analysis.nodes['v_pn'] + analysis.nodes['v_np'] + analysis.nodes['v_nn']) / 4

    gain_cm = vout_cm / vin_cm
    gain_cm_db = 20 * np.log10(np.abs(gain_cm))

    cmrr_db = gain_dm_db - gain_cm_db
    cmrr_1k = np.interp(1e3, freq, cmrr_db)  # CMRR at 1kHz

    measurement_results['CMRR_dB'] = float(cmrr_1k)

    if plots and log_dir is not None:
        _, ax = plt.subplots(figsize=(12, 8))

        ax.semilogx(freq, cmrr_db, color='blue', linestyle='-')
        ax.set_ylabel('CMRR (dB)')
        ax.set_xlabel('Frequency (Hz)')
        ax.grid(True, which="both", ls="-")
        ax.set_title("CMRR Plot of FDDA-CMFB")

        ticks = [0.1, 1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
        labels = ['0.1', '1', '10', '100', '1K', '10K', '100K', '1M', '10M', '100M']
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FixedFormatter(labels)) 

        plt.savefig(os.path.join(log_dir, 'CMRR_plot.png'))
        plt.tight_layout()

    # Hit the Ngspice C-API Reset Button directly
    ngspice_c_lib.ngSpice_Reset()  
    ngspice = simulator.factory(circuit).ngspice  # Re-initialize PySpice
    if ngspice:
        # FIX: Force the internal ID back to a standard Python integer (0)
        # so CFFI doesn't choke trying to parse an existing pointer.
        ngspice._ngspice_id = 0 
        ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine

# ========================
# Runs the PSRR simulation
# ========================
def runsim_PSRR(gain_dm_db, measurement_results, plots=False, log_dir=None):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include fdda_cmfb.spice
"""
    circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    # Define VDD as AC source for PSRR analysis
    circuit.V('VDDac', 'VDD', circuit.gnd, 'DC 1.8 AC 1')

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Series feedback with infinite inductor and parallel feedback with infinite capacitor (to ensure proper DC biasing)
    circuit.L('LFB1', 'V_PN', 'V_OP', 4@u_GH)
    circuit.L('LFB2', 'V_NN', 'V_ON', 4@u_GH)
    circuit.C('CFB1', 'V_PN', circuit.gnd, 4@u_GF)
    circuit.C('CFB2', 'V_NN', circuit.gnd, 4@u_GF)

    # Define DC Inputs (Quiescent Points)
    circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
    except Exception as e:
        raise e

    freq = np.array(analysis.frequency)
    vout_ps = analysis.nodes['v_op'] - analysis.nodes['v_on']
    vdd_ac  = analysis.nodes['vdd']

    gain_ps = vout_ps / vdd_ac
    gain_ps_db = 20 * np.log10(np.abs(gain_ps))

    psrr_db = gain_dm_db - gain_ps_db
    psrr_1k = np.interp(1e3, freq, psrr_db)  # PSRR at 1kHz

    measurement_results['PSRR_dB'] = float(psrr_1k)

    if plots and log_dir is not None:
        _, ax = plt.subplots(figsize=(12, 8))

        ax.semilogx(freq, psrr_db, color='blue', linestyle='-')
        ax.set_ylabel('PSRR (dB)')
        ax.set_xlabel('Frequency (Hz)')
        ax.grid(True, which="both", ls="-")
        ax.set_title("PSRR Plot of FDDA-CMFB")

        ticks = [0.1, 1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
        labels = ['0.1', '1', '10', '100', '1K', '10K', '100K', '1M', '10M', '100M']
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FixedFormatter(labels))

        ax.axhline(y=0, color='red', linestyle='--')  

        plt.savefig(os.path.join(log_dir, 'PSRR_plot.png'))
        plt.tight_layout()

    # Hit the Ngspice C-API Reset Button directly
    ngspice_c_lib.ngSpice_Reset()  
    ngspice = simulator.factory(circuit).ngspice  # Re-initialize PySpice
    if ngspice:
        # FIX: Force the internal ID back to a standard Python integer (0)
        # so CFFI doesn't choke trying to parse an existing pointer.
        ngspice._ngspice_id = 0 
        ngspice._init_ngspice(False)  # Safely re-hook into the wiped C-engine

# ===========================================================
# Top-level function to evaluate a design given the variables
# ===========================================================
def evaluate_design(current_params, plots=False, log_dir=None):
    """
    Accepts the generated variables, runs the simulation, 
    and returns the binary result.
    """

    # Round all parameters to required decimal places
    rounded_params = {
        'W_1': np.round(current_params['W_1'], 2), 'L_1': np.round(current_params['L_1'], 2),
        'W_2': np.round(current_params['W_2'], 2), 'L_2': np.round(current_params['L_2'], 2),
        'W_3': np.round(current_params['W_3'], 2), 'L_3': np.round(current_params['L_3'], 2),
        'W_4': np.round(current_params['W_4'], 2), 'L_4': np.round(current_params['L_4'], 2),
        'W_5': np.round(current_params['W_5'], 2), 'L_5': np.round(current_params['L_5'], 2),
        'W_6': np.round(current_params['W_6'], 2), 'L_6': np.round(current_params['L_6'], 2),
        'W_7': np.round(current_params['W_7'], 2), 'L_7': np.round(current_params['L_7'], 2),
        'W_8': np.round(current_params['W_8'], 2), 'L_8': np.round(current_params['L_8'], 2),
        'V_B1': np.round(current_params['V_B1'], 4),
        'V_B2': np.round(current_params['V_B2'], 4),
        'V_B3': np.round(current_params['V_B3'], 4),
        'V_B4': np.round(current_params['V_B4'], 4),
        'V_CM': np.round(current_params['V_CM'], 2)
    }
    
    # Create a new results dictionary for this specific run
    current_results = {}
    specs_met = False  # Initialize as False, will be updated later

    # Run the sequence
    try:
        generate_spice(rounded_params)  # Generate the SPICE file for the current parameters
        
        # Run the AC simulation and verify gain, gain-bandwidth, and phase margin specs
        gain_dm_db = runsim_AC(measurement_results=current_results, plots=plots, log_dir=log_dir)
        specs_met = (current_results['Gain_dB'] >= Gain_dc_spec_dB and
                        current_results['GBW'] >= GBW_spec and
                        current_results['PM'] >= PM_spec)

        # Only if past specs are met, run the SLEW simulation and verify slew rate spec
        if specs_met:
            runsim_SLEW(measurement_results=current_results, plots=plots, log_dir=log_dir)
            specs_met = (current_results['SR'] >= SR_spec)

        # Only if past specs are met, run the OP simulation and verify power spec
        if specs_met:
            # Run the OP simulation and verify specs
            runsim_OP(measurement_results=current_results, plots=plots, log_dir=log_dir)
            specs_met = (current_results['Power'] <= Power_spec)

        # Only if past specs are met, run the CMRR simulation and verify CMRR spec
        if specs_met:
            runsim_CMRR(gain_dm_db, measurement_results=current_results, plots=plots, log_dir=log_dir)
            specs_met = (current_results['CMRR_dB'] >= CMRR_spec_dB)

        # Only if past specs are met, run the PSRR simulation and verify PSRR spec
        if specs_met:
            runsim_PSRR(gain_dm_db, measurement_results=current_results, plots=plots, log_dir=log_dir)
            specs_met = (current_results['PSRR_dB'] >= PSRR_spec_dB)

        Area_active = get_Area(rounded_params, rounded_params)
        current_results['Area'] = Area_active
        
        # Add current_params to current_results for better traceability
        for key, value in rounded_params.items():
            current_results[key] = value
        if 'V_CM' in current_results:
            del current_results['V_CM']

        return specs_met, current_results
        
    except Exception as e:  # Simulation failed for params
        return False, None  # Return as an infeasible solution
