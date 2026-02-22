import os
from time import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

import PySpice.Spice.NgSpice.Shared as Shared
dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(dir, "..", "ngspice-42_dll_64", "Spice64_dll", "dll-vs", "ngspice{}.dll")
Shared.NgSpiceShared.LIBRARY_PATH = os.path.abspath(dll_path)

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
        # If the crash happened during the 'run' command, it's the stderr bug.
        # We silently pass and let PySpice continue retrieving the vectors!
        if command == 'run':
            pass 
        else:
            raise e # If it's a real syntax error, crash normally

# Apply the patch globally
Shared.NgSpiceShared.exec_command = _patched_exec_command
# =============================================================

logger = Logging.setup_logging()

params = {'W_1': 88, 'L_1': 1,
          'W_2': 88, 'L_2': 1,
          'W_3': 88, 'L_3': 1,
          'W_4': 14, 'L_4': 1,
          'W_5': 28, 'L_5': 1,
          'W_6': 176, 'L_6': 1,
          'W_7': 14, 'L_7': 1,
          'W_8': 176, 'L_8': 1,
          'V_B1': 0.7454,
          'V_B2': 0.6351,
          'V_B3': 0.8571,
          'V_B4': 0.5706,
          'V_CM': 0.9}

# Generates a hard-coded SPICE file in OPEN-LOOP configuration
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

def run_simulation(mode):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.control
    set no_warning
    set no_note
    save all
.endc

.options ngbehavior=hsa
.options stacksize=64
.options nomodcheck

.param mc_mm_switch=0
.param mc_pr_switch=0
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

    # ============================================
    # Performing DC Gain, GBW, and PM calculations
    # ============================================
    if mode == 'AC':
        # Define AC Input (Differential)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9 AC 1')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC -1')

        simulator = circuit.simulator(temperature=27, nominal_temperature=27)
        simulator.options(klu=1)

        analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')

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

        print(f"\n--- AC ANALYSIS RESULTS ---")
        print(f"Calculated DC Gain: {dc_gain:.2f} dB | Calculated GBW: {gbw/1e6:.2f} MHz | Calculated PM: {phase_margin:.2f} degrees")
        
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

        plt.savefig('Gain_and_GBW_plot.png')
        plt.tight_layout()       

    # ================================
    # Performing the Power calculation
    # ================================
    if mode == 'OP':
        # Define DC Inputs (Quiescent Points)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9')

        simulator = circuit.simulator(temperature=27, nominal_temperature=27)
        simulator.options(klu=1)

        analysis = simulator.operating_point()

        iq = float(analysis.branches['vvdd'][0])
        Vout = float(analysis.nodes['v_op'][0])
        power = abs(iq) * 1.8

        print(f"\n--- OP ANALYSIS RESULTS ---")
        print(f"Output DC Voltage: {Vout:.5f} V")
        print(f"Quiescent Current: {abs(iq)*1e6:.2f} uA")
        print(f"Power Consumption: {power*1e6:.2f} uW")

    # ====================================
    # Performing the Slew Rate calculation
    # ====================================
    if mode == 'SLEW':
        # Remove the series/parallel feedback inductors/capacitors for slew rate analysis
        circuit._elements.pop('LLFB1')
        circuit._elements.pop('LLFB2')
        circuit._elements.pop('CCFB1')
        circuit._elements.pop('CCFB2')
        # Form the closed-loop configuration (Unity gain)
        circuit.R('RFB1', 'V_PN', 'V_OP', 0@u_Ohm)
        circuit.R('RFB2', 'V_NN', 'V_ON', 0@u_Ohm)
        # Define Pulse Inputs (Differential)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0 PULSE(0 1.8 10u 10p 10p 20u 40u)')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 1.8 PULSE(1.8 0 10u 10p 10p 20u 40u)')

        simulator = circuit.simulator(temperature=27, nominal_temperature=27)
        simulator.options(klu=1, method='gear')

        analysis = simulator.transient(step_time=10@u_ns, end_time=13@u_us, start_time=7@u_us, use_initial_condition=True)

        time = np.array(analysis.time)
        vin = analysis.nodes['v_pp'] - analysis.nodes['v_np']
        vout = analysis.nodes['v_op'] - analysis.nodes['v_on']
        
        v_min = np.interp(9e-6, time, vout)   # Voltage at 9μs
        v_max = np.interp(12e-6, time, vout)  # Voltage at 12μs

        v_swing = float(v_max) - float(v_min)
        v_10 = float(v_min) + (0.1 * v_swing)
        v_90 = float(v_max) - (0.1 * v_swing)

        t_10 = np.interp(v_10, vout, time)
        t_90 = np.interp(v_90, vout, time)

        slew = (v_90 - v_10) / (t_90 - t_10)
        slew_us = slew / 1e6  # Convert to V/μs

        print(f"\n--- SLEW ANALYSIS RESULTS ---")
        print(f"Measured Slew Rate: {slew_us:.2f} V/μs")
        
        _, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.plot(time*1e6, vin, color='blue', linestyle='-')
        ax1.set_ylabel('Input Voltage (V)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("FDDA-CMFB Slew Response")

        ax2.plot(time*1e6, vout, color='blue', linestyle='-')
        ax2.set_ylabel('Output Voltage (V)')
        ax2.set_xlabel('Time (μs)')
        ax2.grid(True, which="both", ls="-")

        if slew_us > 0:
            ax2.scatter([t_10*1e6, t_90*1e6], [v_10, v_90], color='black', zorder=5)

        plt.savefig('Slew_plot.png')
        plt.tight_layout()

    # ===============================
    # Performing the PSRR calculation
    # ===============================
    if mode == 'PSRR':
        # # Redefine the circuit with mismatch for CMRR analysis
        # circuit._elements.pop('XX1')
        # circuit.X('X1', 'FDDA_PSRR', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')

        # Define AC Input (Differential)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9 AC 1')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC -1')

        sim_dm = circuit.simulator(temperature=27, nominal_temperature=27)
        sim_dm.options(klu=1)

        dm_analysis = sim_dm.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')

        freq = np.array(dm_analysis.frequency)
        vout_dm = dm_analysis.nodes['v_op'] - dm_analysis.nodes['v_on']
        vin_dm  = (dm_analysis.nodes['v_pp'] - dm_analysis.nodes['v_pn']) - (dm_analysis.nodes['v_np'] - dm_analysis.nodes['v_nn'])

        gain_dm = vout_dm / vin_dm
        gain_dm_db = 20 * np.log10(np.abs(gain_dm))

        for name in ['VVPP', 'VVNP']:
            circuit._elements.pop(name)
        # Define DC Inputs (Quiescent Points)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9')
        # Redefine VDD as AC source for PSRR analysis
        circuit._elements.pop('VVDD')
        circuit.V('VDDac', 'VDD', circuit.gnd, 'DC 1.8 AC 1')

        sim_ps = circuit.simulator(temperature=27, nominal_temperature=27)
        sim_ps.options(klu=1)

        ps_analysis = sim_ps.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')

        freq = np.array(ps_analysis.frequency)
        vout_ps = ps_analysis.nodes['v_op'] - ps_analysis.nodes['v_on']
        vdd_ac  = ps_analysis.nodes['vdd']

        gain_ps = vout_ps / vdd_ac
        gain_ps_db = 20 * np.log10(np.abs(gain_ps))

        psrr_db = gain_dm_db - gain_ps_db
        # PSRR at 1kHz
        psrr_1k = np.interp(1e3, freq, psrr_db)

        print(f"\n--- PSRR ANALYSIS RESULTS ---")
        print(f"PSRR at 1kHz: {psrr_1k:.2f} dB")
        
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

        plt.savefig('PSRR_plot.png')
        plt.tight_layout()

    # ===============================
    # Performing the CMRR calculation
    # ===============================
    if mode == 'CMRR':
        # # Redefine the circuit with mismatch for CMRR analysis
        # circuit._elements.pop('XX1')
        # circuit.X('X1', 'FDDA_CMRR', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')

        # Define AC Input (Differential)
        circuit.V('VPP', 'V_PP', circuit.gnd, 'DC 0.9 AC 1')
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC -1')

        sim_dm = circuit.simulator(temperature=27, nominal_temperature=27)
        sim_dm.options(klu=1)

        dm_analysis = sim_dm.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')

        freq = np.array(dm_analysis.frequency)
        vout_dm = dm_analysis.nodes['v_op'] - dm_analysis.nodes['v_on']
        vin_dm  = (dm_analysis.nodes['v_pp'] - dm_analysis.nodes['v_pn']) - (dm_analysis.nodes['v_np'] - dm_analysis.nodes['v_nn'])

        gain_dm = vout_dm / vin_dm
        gain_dm_db = 20 * np.log10(np.abs(gain_dm))

        circuit._elements.pop('VVNP')
        # Define AC Input (Common Mode)
        circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9 AC 1')

        sim_cm = circuit.simulator(temperature=27, nominal_temperature=27)
        sim_cm.options(klu=1)

        cm_analysis = sim_cm.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        
        freq = np.array(cm_analysis.frequency)
        vout_cm = cm_analysis.nodes['v_op'] - cm_analysis.nodes['v_on']
        vin_cm  = (cm_analysis.nodes['v_pp'] + cm_analysis.nodes['v_pn'] + cm_analysis.nodes['v_np'] + cm_analysis.nodes['v_nn']) / 4

        gain_cm = vout_cm / vin_cm
        gain_cm_db = 20 * np.log10(np.abs(gain_cm))

        cmrr_db = gain_dm_db - gain_cm_db
        # CMRR at 1kHz
        cmrr_1k = np.interp(1e3, freq, cmrr_db)
        
        print(f"\n--- CMRR ANALYSIS RESULTS ---")
        print(f"CMRR at 1kHz: {cmrr_1k:.2f} dB")
        
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

        # ax.axhline(y=0, color='red', linestyle='--') 

        plt.savefig('CMRR_plot.png')
        plt.tight_layout()

# Measure start time
start_time = time()

generate_spice(params)
run_simulation('AC')
run_simulation('OP')
run_simulation('SLEW')
run_simulation('PSRR')
run_simulation('CMRR')

# Measure end time and calculate elapsed time
end_time = time()
elapsed_time = end_time - start_time
print(f"\nTotal Simulation Time: {elapsed_time:.2f} seconds")