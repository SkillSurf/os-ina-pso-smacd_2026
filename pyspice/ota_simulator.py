import PySpice.Spice.NgSpice.Shared as NgSpiceSharedModule
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

import numpy as np
import matplotlib.pyplot as plt

from PySpice.Plot.BodeDiagram import bode_diagram
from PySpice.Probe.Plot import plot
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()

NgSpiceSharedModule.NgSpiceShared.NGSPICE_SUPPORTED_VERSION = 42 
# ngspice = NgSpiceShared()

# --- 1. Create a dummy .spice file for the OTA (Simulating your teammate's output) ---
# with open('simple_ota.spice', 'w') as f:
#     f.write('''
# .SUBCKT my_ota in_p in_n out vdd vss
# * Simple behavioral model of an OTA
# G1 0 out in_p in_n 1m
# R1 out 0 1Meg
# C1 out 0 10pF
# .ENDS
#     ''')

SIM_MODE = 'OP'     #Options: AC, TRANS, SLEW, OP

def validate_environment(pdk_path):
    print("--- PRE-FLIGHT VALIDATION ---")
    
    # Inject initialization commands directly to engine memory
    # 'hsa' mode is required for sky130's complex math (int, limit, etc.)
    ngspice.exec_command('set ngbehavior=hsa')
    ngspice.exec_command('set xspice_empty_vector_replacement=0')
    ngspice.exec_command('set stacksize=64') # Prevents memory crash on deep subcircuits
    
    # Warm-load the library
    try:
        ngspice.exec_command(f'lib {pdk_path} tt')
        print(f"Successfully loaded PDK corner 'tt' from: {pdk_path}")
    except Exception as e:
        print(f"Error loading PDK: {e}")
        return False

    # Check if a specific model is loaded in memory
    # We check for the basic 1.8V NFET subcircuit
    test_model = "sky130_fd_pr__nfet_01v8"
    listing = ngspice.exec_command('devhelp').lower()
    
    # Note: devhelp might be huge, so we also check the subcircuit table
    if test_model in listing or "nfet" in listing:
        print(f"Model Check: '{test_model}' appears to be recognized.")
    else:
        print(f"Warning: '{test_model}' not found in devhelp. Trying a test listing...")
    
    return True

def run_simulation(mode):

    circuit = Circuit('Hybrid OTA Simulation')
    circuit.raw_spice ="""
.options ngbehavior=hsa
.options stacksize=64
.options nomodcheck
.param mc_mm_switch=0
.param mc_pr_switch=0
.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /foss/designs/cmos_ina_sky130/Opamp.spice
"""

    pdk_path = '/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice'
    # circuit.lib('/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice', 'tt')
    # if not validate_environment(pdk_path):
    #     return

    # circuit.include('Opamp.spice')

    opamp_params = {
        'W_in': 4, 'L_in': 1, 'nf_in': 4, 'm_in': 2,
        'W_load': 4, 'L_load': 1, 'nf_load': 4, 'm_load': 4,
        'W_drive': 4, 'L_drive': 1, 'nf_drive': 4, 'm_drive': 7,
        'W_tail': 4, 'L_tail': 1, 'nf_tail': 4, 'm_tail': 8,
        'Cc': '2pF', 'Rz': 60
    }

    # circuit.X('OTA1', 'my_ota', 'VDD', 'Vp', 'Vn', 'Vout', 'VSS')
    circuit.X('X1', 'Opamp', 'VDD', 'Vp', 'Vn', 'Vout', 'Ibias', 'VSS', 
          L_in=1.0@u_um, W_in=4.0@u_um, nf_in=4, m_in=1,
          L_load=1.0@u_um, W_load=4.0@u_um, nf_load=4, m_load=2,
          L_drive=1.0@u_um, W_drive=4.0@u_um, nf_drive=4, m_drive=7,
          L_tail=1.0@u_um, W_tail=4.0@u_um, nf_tail=4, m_tail=8,
          Cc=2.0@u_pF, Rz=60)
    circuit.C('load', 'Vout', 'VSS', 5@u_pF)

    circuit.V('vdd', 'VDD', circuit.gnd, 1.8@u_V)
    circuit.V('vss', 'VSS', circuit.gnd, 0@u_V)
    circuit.I('bias', 'VDD', 'Ibias', 5@u_uA)

    # circuit.V('gnd_link', 'GND', circuit.gnd, 0@u_V)

    if mode == 'AC':        # Define AC Input (Differential)
        circuit.V('input', 'Vp', 'Vn', 'dc 0.9 AC 1')
        circuit.V('cm', 'Vn', circuit.gnd, 0.9@u_V)

        simulator = circuit.simulator(simulator='ngspice-subprocess', temperature=25)
        print(simulator.ngspice.listing())

        analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')

        freq = np.array(analysis.frequency)
        gain_db = 20 * np.log10(np.absolute(analysis.out))
        phase_deg = np.angle(analysis.out, deg=True)        # Use deg=True here because built-in bode_diagram expects degrees
        mag_db = 20 * np.log10(np.absolute(analysis.out))
        dc_gain = mag_db[0]
        gbw = np.interp(0, mag_db[::-1], freq[::-1])
        phase_at_gbw = np.interp(gbw, freq, phase_deg)
        phase_margin = 180 + phase_at_gbw

        print(f"\n--- AC ANALYSIS RESULTS ---")
        print(f"Calculated DC Gain: {dc_gain:.2f} dB | Calculated GBW: {gbw/1e6:.2f} MHz | Calculated PM: {phase_margin:.2f} degrees")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.semilogx(freq, gain_db, color='blue', marker='.', linestyle='-')
        ax1.set_ylabel('Gain (dB)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("Bode Diagram of Biomedical INA")

        ax2.semilogx(freq, phase_deg, color='blue', marker='.', linestyle='-')
        ax2.set_ylabel('Phase (Degrees)')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.grid(True, which="both", ls="-")

        ax1.axhline(y=0, color='red', linestyle='--') 
        ax2.axhline(y=-180, color='red', linestyle='--') 

        plt.savefig('Gain_and_GBW_plot.png')
        plt.tight_layout()
        plt.show()
    
    elif mode == 'OP':
        circuit.V('vp', 'Vp', circuit.gnd, 'SIN(0.9V 1mV 100kHz)')
        circuit.V('vn', 'Vn', circuit.gnd, 'SIN(0.9V 1mV 100kHz)')

        simulator = circuit.simulator(simulator='ngspice-subprocess')

        try:
            analysis = simulator.operating_point()
            print(f"Success! Vout: {analysis.nodes['vout'][0]:.4f} V")
        except Exception as e:
            # If it fails, we finally look at the internal Ngspice error buffer
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            # Access the shared instance to see what went wrong inside
            # print(NgSpiceShared.get_instance().stdout)
            print(e)
            raise e

        iq = float(analysis.branches['vVDD'][0])
        v_out = float(analysis.nodes['Vout'][0])

        print(f"\n--- OPERATING POINT RESULTS ---")
        print(f"Node 'Vout'  : {v_out:.4f} V")
        print(f"I-Quiescent : {abs(iq)*1e6:.2f} uA")

    elif mode == 'TRANS':
        circuit.V('input_p', 'Vp', circuit.gnd, 'SIN(0.9V 1mV 100Hz)') 
        circuit.V('input_n', 'Vn', circuit.gnd, 'SIN(0.9V -1mV 100Hz)')
        # circuit.V('cm', 'cm_node', circuit.gnd, 0.9@u_V)

        simulator = circuit.simulator()
        analysis = simulator.transient(step_time=10@u_us, end_time=50@u_ms)

        time = np.array(analysis.time)
        vout = np.array(analysis.out)
        vin_p = np.array(analysis.in_p)
        vin_n = np.array(analysis.in_n)

        print(f"\n--- TRANSIENT ANALYSIS ---")
        plt.figure(figsize=(10, 6))
        plt.plot(time * 1e3, vout, label='Output (Vout)') # Changed to ms for 50Hz
        plt.plot(time * 1e3, vin_p - vin_n, label='Input (Vin_diff)', linestyle='--')
        
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage (V)")
        plt.legend()
        plt.title("Transient Analysis: 100Hz Differential Response")
        plt.grid(True)
        plt.savefig('Transient_analysis.png')
        plt.show()

    elif mode == 'SLEW':
        circuit.V('input_p', 'Vp', circuit.gnd, 'PULSE(0.9V 1.1V 150n 1n 1n 2500n 5000n)')
        circuit.V('input_n', 'Vn', circuit.gnd, 'PULSE(0.9V 0.7V 150n 1n 1n 2500n 5000n)')
        simulator = circuit.simulator()
        analysis = simulator.transient(step_time=10@u_ns, end_time=50@u_us)
        
        time = np.array(analysis.time)
        vout = np.array(analysis.out)
        sr = np.max(np.diff(vout) / np.diff(time))
        
        print(f"\n--- SLEW RATE ---")
        print(f"Measured Slew Rate: {sr/1e6:.2f} V/us")
        
        plt.plot(time*1e6, vout)
        plt.xlabel("Time (us)")
        plt.ylabel("Output (V)")
        plt.title("Step Response")
        plt.savefig('Slewrate_positive_openloop.png')
        plt.show()

# op_params = {
#     'mult_in': 1,
#     'mult_load': 2,
#     'mult_5': 8,
#     'mult_6': 7,
#     'mult_7_10': 11,
#     'mult_8': 1,
#     'mult_9_11': 6,
#     'cap_mf': 2,
#     'r_w': 0.04,
#     'r_l': 60
# }

# run_simulation(op_params,SIM_MODE)
run_simulation('OP')
# run_simulation('TRANS')
# run_simulation('SLEW')
