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

SIM_MODE = 'OP'     #Options: AC, TRANS, SLEW, OP

def generate_spice_file(params):
    """Generates a hard-coded Opamp.spice file to avoid parameter parsing errors."""
    def get_geom_string(w, nf):

        w_val = float(w)
        nf_val = int(nf)
        
        return (
            f"W={w_val} nf={nf_val} "
            f"ad='int(({nf_val}+1)/2) * {w_val}/{nf_val} * 0.29' "
            f"as='int(({nf_val}+2)/2) * {w_val}/{nf_val} * 0.29' "
            f"pd='2*int(({nf_val}+1)/2) * ({w_val}/{nf_val} + 0.29)' "
            f"ps='2*int(({nf_val}+2)/2) * ({w_val}/{nf_val} + 0.29)' "
            f"nrd='0.29 / {w_val}' nrs='0.29 / {w_val}'"
        )

    # Individual geometry strings for every group
    g_in    = get_geom_string(params['W_in'], params['nf_in'])
    g_load  = get_geom_string(params['W_load'], params['nf_load'])
    g_tail  = get_geom_string(params['W_tail'], params['nf_tail'])
    g_drive = get_geom_string(params['W_drive'], params['nf_drive'])
    
    # Using specific dimensions for XM8 to maintain bias stability
    g_bias  = get_geom_string(params.get('W_bias', 4.35), params.get('nf_bias', 4))

    content = f"""* 2-Stage Miller Compensated Opamp (Auto-generated)
.subckt Opamp VDD Vp Vn Vout Ibias VSS

* --- STAGE 1: Differential Pair ---
XM1 net1 Vn Itail VSS sky130_fd_pr__nfet_01v8 L={params['L_in']} {g_in} m={params['m_in']} sa=0 sb=0 sd=0 mult=1
XM2 Vouts1 Vp Itail VSS sky130_fd_pr__nfet_01v8 L={params['L_in']} {g_in} m={params['m_in']} sa=0 sb=0 sd=0 mult=1

* Current Mirror Load (PMOS)
XM3 net1 net1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_load']} {g_load} m={params['m_load']} sa=0 sb=0 sd=0 mult=2
XM4 Vouts1 net1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_load']} {g_load} m={params['m_load']} sa=0 sb=0 sd=0 mult=2

* Tail Current Source (NMOS)
XM5 Itail Ibias VSS VSS sky130_fd_pr__nfet_01v8 L={params['L_tail']} {g_tail} m={params['m_tail']} sa=0 sb=0 sd=0 mult=8

* --- STAGE 2: Common Source Output ---
XM6 Vout Vouts1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_drive']} {g_drive} m={params['m_drive']} sa=0 sb=0 sd=0 mult=7
XM7 Vout Ibias VSS VSS sky130_fd_pr__nfet_01v8 L={params['L_tail']} {g_tail} m={params['m_tail']} sa=0 sb=0 sd=0 mult=8

* --- Bias Diode ---
XM8 Ibias Ibias VSS VSS sky130_fd_pr__nfet_01v8 L={params.get('L_bias', 1.25)} {g_bias} m=1 sa=0 sb=0 sd=0 mult=1

* --- Compensation Network ---
C1 Vout net_comp {params['Cc']}
R1 net_comp Vouts1 {params['Rz']}

.ends
"""
    with open('Opamp_dynamic.spice', 'w') as f:
        f.write(content)



def run_simulation(mode):

    circuit = Circuit('Hybrid OTA Simulation')
    circuit.raw_spice ="""
.options ngbehavior=hsa
.options stacksize=64
.options nomodcheck
.param mc_mm_switch=0
.param mc_pr_switch=0
.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /foss/designs/cmos_ina_sky130/Opamp_dynamic.spice
"""
    # pdk_path = '/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice'
    # circuit.lib('/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice', 'tt')
    # circuit.include('Opamp.spice')

    circuit.X('X1', 'Opamp', 'VDD', 'Vp', 'Vn', 'Vout', 'Ibias', 'VSS')
    
    circuit.V('vdd', 'VDD', circuit.gnd, 1.8@u_V)
    circuit.V('vss', 'VSS', circuit.gnd, 0@u_V)
    circuit.I('bias', 'VDD', 'Ibias', 5@u_uA)
    circuit.C('load', 'Vout', 'VSS', 1@u_pF) # Per Specification Table
    circuit.R('dc_fix', 'Vout', 'VSS', 10@u_MOhm) # High-Z load for OP stability


    if mode == 'AC':        # Define AC Input (Differential)
        circuit.V('input', 'Vp', 'Vn', 'dc 0.9 AC 1')
        circuit.V('cm', 'Vn', circuit.gnd, 0.9@u_V)

        simulator = circuit.simulator(simulator='ngspice-subprocess', temperature=25)

        try:
            analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        except Exception as e:
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            print(e)
            raise e
        
        op_analysis = simulator.operating_point()
        i_total = abs(float(op_analysis.branches['vvdd'][0]))
        power_uw = i_total * 1.8 * 1e6  # Power = VDD * I_total

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

        # Comparing with the specs
        specs = {
            "Open-loop gain": {"val": dc_gain, "target": 70, "unit": "dB", "op": ">="},
            "GBW": {"val": gbw/1e6, "target": 30, "unit": "MHz", "op": ">="},
            "Phase Margin": {"val": pm, "target": 60, "unit": "deg", "op": ">"},
            "Power Total": {"val": power_uw, "target": 500, "unit": "uW", "op": "<="}
        }

        print(f"\n--- Results for L={design_params['L_in']}, W={design_params['W_in']} ---")
        all_passed = True
        for key, s in specs.items():
            passed = (s['val'] >= s['target']) if s['op'] == ">=" else (s['val'] <= s['target'])
            if s['op'] == ">": passed = s['val'] > s['target']
            
            status = "PASS" if passed else "FAIL"
            if not passed: all_passed = False
            print(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}")
        
        return all_passed

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

params = {
    'W_in': 4, 'L_in': 1, 'nf_in': 4, 'm_in': 1,
    'W_load': 4, 'L_load': 1, 'nf_load': 4, 'm_load': 2,
    'W_drive': 4, 'L_drive': 1, 'nf_drive': 4, 'm_drive': 7,
    'W_tail': 4, 'L_tail': 1, 'nf_tail': 4, 'm_tail': 8,
    'W_bias': 4.35, 'L_bias': 1.25, 'nf_bias': 4, 'm_bias': 1,
    'Cc': '2pF', 'Rz': 60
}

generate_spice_file(params)

run_simulation('AC')
run_simulation('OP')
run_simulation('TRANS')
run_simulation('SLEW')




# def validate_environment(pdk_path):
#     print("--- PRE-FLIGHT VALIDATION ---")
    
#     # Inject initialization commands directly to engine memory
#     # 'hsa' mode is required for sky130's complex math (int, limit, etc.)
#     ngspice.exec_command('set ngbehavior=hsa')
#     ngspice.exec_command('set xspice_empty_vector_replacement=0')
#     ngspice.exec_command('set stacksize=64') # Prevents memory crash on deep subcircuits
    
#     # Warm-load the library
#     try:
#         ngspice.exec_command(f'lib {pdk_path} tt')
#         print(f"Successfully loaded PDK corner 'tt' from: {pdk_path}")
#     except Exception as e:
#         print(f"Error loading PDK: {e}")
#         return False

#     # Check if a specific model is loaded in memory
#     # We check for the basic 1.8V NFET subcircuit
#     test_model = "sky130_fd_pr__nfet_01v8"
#     listing = ngspice.exec_command('devhelp').lower()
    
#     # Note: devhelp might be huge, so we also check the subcircuit table
#     if test_model in listing or "nfet" in listing:
#         print(f"Model Check: '{test_model}' appears to be recognized.")
#     else:
#         print(f"Warning: '{test_model}' not found in devhelp. Trying a test listing...")
    
#     return True