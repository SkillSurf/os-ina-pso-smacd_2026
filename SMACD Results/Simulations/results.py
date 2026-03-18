import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, LogLocator
import scienceplots

from params import *

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_V, u_pF, u_GH, u_GF, u_Hz, u_MHz, u_ns, u_us
import PySpice.Spice.NgSpice.Shared as Shared

dir = os.path.dirname(os.path.abspath(__file__))
dll_path = os.path.join(dir, "..", "..", "pyspice", "ngspice-44_dll_64", "Spice64_dll", "dll-vs", "ngspice{}.dll")  # Ngspice 44
Shared.NgSpiceShared.LIBRARY_PATH = os.path.abspath(dll_path)

plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

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
    
    with open('circuit.spice', 'w') as f:
        f.write(spice)

# ======================
# Runs the AC simulation
# ======================
def runsim_AC(measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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
    phase_deg = np.unwrap(np.angle(gain, deg=True), period=360)

    dc_gain = gain_db[0]
    gbw = np.interp(0, gain_db[::-1], freq[::-1])
    phase_at_gbw = np.interp(gbw, freq, phase_deg)
    phase_margin = 180 + phase_at_gbw

    measurement_results['Gain_dB'] = float(dc_gain)
    measurement_results['GBW'] = float(gbw)
    measurement_results['PM'] = float(phase_margin)

    return gain_db, phase_deg, freq

# ======================
# Runs the OP simulation
# ======================
def runsim_OP(measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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
    # v_cmfb = float(analysis.nodes['v_cmfb'][0])

    measurement_results['Power'] = power
    # measurement_results['V_CMFB'] = v_cmfb

    # Write all operating point values to a text file
    with open('Plots/OPERATING_POINT.txt', 'w') as f:
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

# ========================
# Runs the SLEW simulation
# ========================
def runsim_SLEW(measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # # Form the closed-loop configuration (Unity gain)
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_OP', 'V_NP', 'V_ON', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_OP', 'V_NP', 'V_ON', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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
    measurement_results['Out_Swing'] = float(v_swing)

    with plt.style.context(['science', 'ieee']):

        # Plot the transient slew response
        fig, ax = plt.subplots()

        l1 = ax.plot(time*1e6, vin, label='Input', color='blue', linestyle='--')
        l2 = ax.plot(time*1e6, vout, label='Output', color='red', linestyle='-')

        ax.scatter([t_10*1e6, t_90*1e6], [v_10, v_90], color='black', zorder=5, s=5)
        ax.axvline(x=t_90*1e6, color='black', linestyle='--', linewidth=0.5)
        ax.axhline(y=v_10, color='black', linestyle='--', linewidth=0.5)

        ax.set_xlabel(r'Time [$\mu$s]')
        ax.set_ylabel(r'Voltage [V]')

        ax.set_xlim(0, 20)
        ax.set_ylim(-2, 2)

        ax.set_yticks([-1.8, -1.2, -0.6, 0, 0.6, 1.2, 1.8])
        ax.set_xticks([0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20])        

        lns = l1 + l2
        ax.legend(lns, [l.get_label() for l in lns], loc='best')

        fig.set_figheight(2)
        plt.tight_layout()
        plt.savefig('Plots/SLEW_RESPONSE.pdf', format='pdf', bbox_inches='tight')

# ========================
# Runs the CMRR simulation
# ========================
def runsim_CMRR(gain_dm_db, measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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

    return cmrr_db

# ========================
# Runs the PSRR simulation
# ========================
def runsim_PSRR(gain_dm_db, measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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

    return psrr_db

# =========================
# Runs the NOISE simulation
# =========================
def runsim_NOISE(measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    # circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB', circuit.gnd, 'V_OP', 'V_ON')
    # circuit.X('X2', 'CMFB', 'V_CMFB', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

    circuit.V('VDD', 'VDD', circuit.gnd, 1.8@u_V)

    circuit.C('LOADP', 'V_OP', circuit.gnd, 2@u_pF)
    circuit.C('LOADN', 'V_ON', circuit.gnd, 2@u_pF)

    # Series feedback with infinite inductor and parallel feedback with infinite capacitor (to ensure proper DC biasing)
    circuit.L('LFB1', 'V_PN', 'V_OP', 4@u_GH)
    circuit.L('LFB2', 'V_NN', 'V_ON', 4@u_GH)
    circuit.C('CFB1', 'V_PN', circuit.gnd, 4@u_GF)
    circuit.C('CFB2', 'V_NN', circuit.gnd, 4@u_GF)

    # Define AC Input (Single Source)
    circuit.V('VPP', 'V_PP', 'V_NP', 'DC 0 AC 1')
    circuit.V('VNP', 'V_NP', circuit.gnd, 'DC 0.9')

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.noise(
            output_node='V_OP',
            ref_node='V_ON',
            src='VVPP',
            variation='dec',
            points=20,
            start_frequency=0.1@u_Hz, 
            stop_frequency=100@u_MHz,
            )
    except Exception as e:
        raise e

    measurement_results['Noise_RMS'] = float(analysis.nodes['inoise_total'][0])
    noise1_plot = simulator.ngspice.plot(simulation=simulator, plot_name='noise1')
    
    freq = np.array(noise1_plot['frequency']._data)
    noise = np.array(noise1_plot['inoise_spectrum']._data)

    noise_1k = np.interp(1e3, freq, noise)  # Noise Input at 1kHz

    measurement_results['Noise_in'] = float(noise_1k)

    with plt.style.context(['science', 'ieee', 'grid']):

        # Plot the noise spectrum
        fig, ax = plt.subplots()

        ax.loglog(freq, noise, color='black', linestyle='-')

        ax.scatter([1e3], [noise_1k], color='red', zorder=5, s=5)
        ax.axvline(x=1e3, color='red', linestyle='--', linewidth=0.5)
        ax.axhline(y=noise_1k, color='red', linestyle='--', linewidth=0.5)

        ax.set_xlabel(r'Frequency [Hz]')
        ax.set_ylabel(r'Input-Referred Noise [V/$\sqrt{\text{Hz}}$]')

        ax.set_xlim(1e-1, 1e8)
        ax.set_ylim(10**np.floor(np.log10(min(noise))), 10**np.ceil(np.log10(noise[0])))

        ax.set_xticks([1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000])

        ax.grid(True, axis='both', which='major', linestyle='-', alpha=0.3)
        ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), numticks=12))
        ax.grid(True, axis='both', which='minor', linestyle=':', alpha=0.2)
        
        fig.set_figheight(2)
        plt.tight_layout()
        plt.savefig('Plots/NOISE_SPECTRUM.pdf', format='pdf', bbox_inches='tight') 

    return

# ========================
# Runs the CMFB simulation
# ========================
def runsim_CMFB(measurement_results):

    circuit = Circuit('FDDA_CMFB Simulation')
    circuit.raw_spice ="""
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include circuit.spice
.include lvs.spice
.include pex.spice
"""
    circuit.X('X1', 'FDDA', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'VDD', 'V_CMFB_IN', circuit.gnd, 'V_OP', 'V_ON')
    circuit.X('X2', 'CMFB', 'V_CMFB_OUT', 'V_OP', 'V_ON', circuit.gnd, 'VDD')

    # circuit.X('X1', 'FDDA_CMFB_PEX', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    # circuit.X('X1', 'FDDA_CMFB', 'V_B2', 'VDD', circuit.gnd, 'V_B4', 'V_B3', 'V_B1', 'V_PP', 'V_PN', 'V_NP', 'V_NN', 'V_OP', 'V_CM', 'V_ON')
    # circuit.V('VB1', 'V_B1', circuit.gnd, 0.7056@u_V)
    # circuit.V('VB2', 'V_B2', circuit.gnd, 0.7057@u_V)
    # circuit.V('VB3', 'V_B3', circuit.gnd, 1.0395@u_V)
    # circuit.V('VB4', 'V_B4', circuit.gnd, 0.3061@u_V)
    # circuit.V('VCM', 'V_CM', circuit.gnd, 0.9@u_V)

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

    # Connect the CMFB input and output with an ideal inductor to measure the CMFB loop gain
    circuit.L('LCM', 'V_CMFB_IN', 'V_CMFB_OUT', 4@u_GH)

    # Define AC input at the CMFB node
    circuit.V('VAC', 'V_IN', circuit.gnd, 'DC 0 AC 1')
    circuit.C('CCM', 'V_CMFB_IN', 'V_IN', 4@u_GF)

    simulator = circuit.simulator(temperature=27, nominal_temperature=27)

    try:
        analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
    except Exception as e:
        raise e
    
    freq = np.array(analysis.frequency)
    vout = analysis.nodes['v_cmfb_out']
    vin  = analysis.nodes['v_cmfb_in']

    gain = vout / vin
    gain_db = 20 * np.log10(np.abs(gain))
    phase_deg = np.angle(gain, deg=True)

    dc_gain = gain_db[0]
    gbw = np.interp(0, gain_db[::-1], freq[::-1])
    phase_margin = np.interp(gbw, freq, phase_deg)

    measurement_results['CMFB_Gain_dB'] = float(dc_gain)
    measurement_results['CMFB_GBW'] = float(gbw)
    measurement_results['CMFB_PM'] = float(phase_margin)

    return gain_db, phase_deg

# ================================
# Function to calculate total area
# ================================
def get_Area(W, L):

    # Formula for calculating area based on W and L of each transistor
    area = (4 * W['W_1'] * L['L_1']) \
            + (2 * W['W_2'] * L['L_2']) \
            + (2 * W['W_3'] * L['L_3']) \
            + (2 * W['W_4'] * L['L_4']) \
            + (4 * W['W_5'] * L['L_5']) \
            + (2 * W['W_6'] * L['L_6']) \
            + (4 * W['W_7'] * L['L_7']) \
            + (2 * W['W_8'] * L['L_8'])
    
    return area

def create_Plot(freq, fdda_gain_db, fdda_phase, cmrr_db, psrr_db):
    
    with plt.style.context(['science', 'ieee', 'grid']):

        # Plot all frequency dependant parameters in one figure
        fig, ax = plt.subplots()
        tx = ax.twinx()

        l1 = ax.semilogx(freq, fdda_gain_db, label='Gain', color='red', linestyle='-')
        l2 = ax.semilogx(freq, cmrr_db, label='CMRR', color='black', linestyle=':')
        l3 = ax.semilogx(freq, psrr_db, label='PSRR', color='green', linestyle='-.')
        l4 = tx.semilogx(freq, fdda_phase, label='Phase', color='blue', linestyle='--')

        ax.set_ylabel(r'Magnitude [dB]')
        ax.set_xlabel(r'Frequency [Hz]')
        tx.set_ylabel(r'Phase [$^{\circ}$]')

        ax.set_ylim(-25, 125)
        ax.set_xlim(1e-1, 1e8)
        tx.set_ylim(-187.5, 37.5)

        ax.set_yticks([-20, 0, 20, 40, 60, 80, 100, 120])
        tx.set_yticks([-180, -150, -120, -90, -60, -30, 0, 30])
        tx.set_xticks([0.1, 1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000])
        

        ax.grid(True, axis='both', which='major', linestyle='-', alpha=0.2)
        ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), numticks=12))
        ax.grid(True, axis='x', which='minor', linestyle=':', alpha=0.1)
        tx.grid(False)

        lns = l1 + l4 + l2 + l3
        ax.legend(lns, [l.get_label() for l in lns], loc='best')

        fig.set_figheight(2)
        plt.tight_layout()
        plt.savefig('Plots/FREQUENCY_RESPONSE.pdf', format='pdf', bbox_inches='tight')   

# ===========================================================
# Top-level function to evaluate a design given the variables
# ===========================================================
def evaluate_design(current_params, plots=False):
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

    # # Run the sequence
    # generate_spice(rounded_params)  # Generate the SPICE file for the current parameters
    
    # Run the AC simulation and measure gain, gain-bandwidth, and phase margin
    fdda_gain_db, fdda_phase, freq = runsim_AC(measurement_results=current_results)

    # Run the SLEW simulation and measure slew rate
    runsim_SLEW(measurement_results=current_results)

    # Run the OP simulation and measure power
    runsim_OP(measurement_results=current_results)

    # Run the CMRR simulation and measure CMRR
    cmrr_db = runsim_CMRR(fdda_gain_db, measurement_results=current_results)

    # Run the PSRR simulation and measure PSRR
    psrr_db = runsim_PSRR(fdda_gain_db, measurement_results=current_results)

    # Run the Noise simulation and measure input-referred RMS noise voltage
    runsim_NOISE(measurement_results=current_results)

    # Run the CMFB simulation and measure CMFB loop gain and GBW
    cmfb_gain_db, cmfb_phase = runsim_CMFB(measurement_results=current_results)

    create_Plot(freq, fdda_gain_db, fdda_phase, cmrr_db, psrr_db)

    Area_active = get_Area(rounded_params, rounded_params)
    current_results['Area'] = Area_active
    
    # Add current_params to current_results for better traceability
    for key, value in rounded_params.items():
        current_results[key] = value
    if 'V_CM' in current_results:
        del current_results['V_CM']

    return current_results
    
params = {'W_1': 73.91, 'L_1': 0.3,
          'W_2': 0.9, 'L_2': 0.8,
          'W_3': 0.62, 'L_3': 0.8,
          'W_4': 0.75, 'L_4': 3,
          'W_5': 1.95, 'L_5': 2,
          'W_6': 5.12, 'L_6': 1,
          'W_7': 21.08, 'L_7': 0.2,
          'W_8': 4.25, 'L_8': 0.8,
          'V_B1': 0.7056,
          'V_B2': 0.7057,
          'V_B3': 1.0395,
          'V_B4': 0.3061,
          'V_CM': 0.9}

if __name__ == "__main__":

    results = evaluate_design(params, plots=False)

    print(f"\nFDDA Gain: {results['Gain_dB']:.2f} dB")
    print(f"GBW: {results['GBW']*1e-6:.2f} MHz")
    print(f"Phase Margin: {results['PM']:.2f} degrees")
    print(f"Slew Rate: {results['SR']*1e-6:.2f} V/μs")
    print(f"Output Voltage Swing: {results['Out_Swing']:.2f} V")
    print(f"Power: {results['Power']*1e6:.2f} μW")
    print(f"CMRR @ 1kHz: {results['CMRR_dB']:.2f} dB")
    print(f"PSRR @ 1kHz: {results['PSRR_dB']:.2f} dB")
    print(f"Input-Referred Noise @ 1kHz: {results['Noise_in']*1e9:.2f} nV/√Hz")
    print(f"Input-Referred Noise (0.1 Hz to 100 MHz): {results['Noise_RMS']*1e6:.2f} μV RMS")
    print(f"CMFB Loop Gain: {results['CMFB_Gain_dB']:.2f} dB")
    print(f"CMFB GBW: {results['CMFB_GBW']*1e-6:.2f} MHz")
    print(f"CMFB Phase Margin: {results['CMFB_PM']:.2f} degrees")
    print(f"\nArea: {results['Area']:.2f} μm²")