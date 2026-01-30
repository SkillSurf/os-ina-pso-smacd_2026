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
    g_1  = get_geom_string(params['W_1'], params['nf_1'])
    g_2  = get_geom_string(params['W_2'], params['nf_2'])
    g_3  = get_geom_string(params['W_3'], params['nf_3'])
    g_4  = get_geom_string(params['W_4'], params['nf_4'])
    g_5  = get_geom_string(params['W_5'], params['nf_5'])
    g_6  = get_geom_string(params['W_6'], params['nf_6'])
    

    content = f"""* FDDA (Auto-generated)
.subckt FDDA VDD Vpp Vpn Vnp Vnn Vcmfb Vb1 Vb2 Vb3 Vb4 Von Vop
XMP1 net5 Vpp net1 VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP2 net6 Vpn net1 VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP3 net6 Vnp net2 VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP4 net5 Vnn net2 VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP5 net3 Vcmfb VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_2']} {g_2} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP6 net4 Vcmfb VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_2']} {g_2} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP7 Von Vb4 net3 VDD sky130_fd_pr__pfet_01v8 L={params['L_3']} {g_3} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP8 Vop Vb4 net4 VDD sky130_fd_pr__pfet_01v8 L={params['L_3']} {g_3} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP11 net1 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_6']} {g_6} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP12 net2 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_6']} {g_6} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN3 Von Vb3 net5 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN4 Vop Vb3 net6 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN9 net5 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN10 net6 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0
+ mult=1 m=1

.ends
"""
    with open('fdda.spice', 'w') as f:
        f.write(content)



def run_simulation(mode):

    circuit = Circuit('FDDA Simulation')
    circuit.raw_spice ="""
.control
set no_warning
set no_note
.endc

.options ngbehavior=hsa
.options stacksize=64
.options nomodcheck

.param mc_mm_switch=0
.param mc_pr_switch=0
.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /foss/designs/os-ina-pso-mixdes_2026/pyspice/fdda.spice
"""
    # pdk_path = '/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice'
    # circuit.lib('/foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice', 'tt')
    # circuit.include('Opamp.spice')

    circuit.X('X1', 'FDDA', 'VDD', 'Vpp', 'Vpn', 'Vnp', 'Vnn', 'Vcmfb', 'Vb1', 'Vb2', 'Vb3', 'Vb4', 'Von', 'Vop')
    
    circuit.V('vdd', 'VDD', circuit.gnd, 1.8@u_V)
    circuit.V('vb1', 'Vb1', circuit.gnd, 0.776@u_V)
    circuit.V('vb2', 'Vb2', circuit.gnd, 0.665@u_V)
    circuit.V('vb3', 'Vb3', circuit.gnd, 0.898@u_V)
    circuit.V('vb4', 'Vb4', circuit.gnd, 0.579@u_V)
    # circuit.V('vb5', 'Vcmfb', circuit.gnd, 0.762@u_V)
    circuit.R('rcm1', 'Vop', 'Vcm_sense', 1@u_MOhm)
    circuit.R('rcm2', 'Von', 'Vcm_sense', 1@u_MOhm)
    circuit.V('vcm', 'Vcmfb', 'Vcm_sense', 0@u_V)
    
    circuit.C('load_p', 'Vop', circuit.gnd, 1@u_pF)
    circuit.C('load_n', 'Von', circuit.gnd, 1@u_pF)
    



    if mode == 'AC':        # Define AC Input (Differential)
        circuit.V('vpp', 'Vpp', circuit.gnd, 'dc 0.9 ac 0.5')
        circuit.V('vpn', 'Vpn', circuit.gnd, 'dc 0.9 ac -0.5')
        circuit.V('vnp', 'Vnp', circuit.gnd, 'dc 0.9 ac -0.5')
        circuit.V('vnn', 'Vnn', circuit.gnd, 'dc 0.9 ac 0.5')

        simulator = circuit.simulator(simulator='ngspice-subprocess', temperature=25)

        try:
            analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        except Exception as e:
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            print(e)
            raise e
        # .options noopiter
        op_analysis = simulator.operating_point()
        # i_total = abs(float(op_analysis.branches['vvdd'][0]))
        # power_uw = i_total * 1.8 * 1e6  # Power = VDD * I_total

        # Check DC levels before looking at AC results
        print(f"DC Vop: {float(op_analysis.nodes['Vop'][0]):.3f} V")
        print(f"DC Von: {float(op_analysis.nodes['Von'][0]):.3f} V")

        freq = np.array(analysis.frequency)
        vout = analysis.nodes['Vop'] - analysis.nodes['Von']
        vin  = (analysis.nodes['Vpp'] - analysis.nodes['Vpn'])

        gain = vout / vin
        gain_db = 20 * np.log10(np.abs(gain))
        phase_deg = np.angle(gain, deg=True)

        # gain_db = 20 * np.log10(np.absolute(v_diff))
        # phase_deg = np.angle(v_diff, deg=True)        # Use deg=True here because built-in bode_diagram expects degrees
        mag_db = 20 * np.log10(np.absolute(gain))
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
            "Phase Margin": {"val": phase_margin, "target": 60, "unit": "deg", "op": ">"}
            # "Power Total": {"val": power_uw, "target": 500, "unit": "uW", "op": "<="}
        }

        print(f"\n--- Results for L={params['L_1']}, W={params['W_1']} ---")
        all_passed = True
        
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

        for key, s in specs.items():
            passed = (s['val'] >= s['target']) if s['op'] == ">=" else (s['val'] <= s['target'])
            if s['op'] == ">": passed = s['val'] > s['target']
            
            status = "PASS" if passed else "FAIL"
            if not passed: all_passed = False
            print(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}")

        return all_passed
    
    elif mode == 'OP':
        circuit.V('vp', 'Vpp', circuit.gnd, 'SIN(0.9V 1mV 100kHz)')
        circuit.V('vn', 'Vnn', circuit.gnd, 'SIN(0.9V 1mV 100kHz)')

        simulator = circuit.simulator(simulator='ngspice-subprocess')

        try:
            analysis = simulator.operating_point()
            print(f"Success! Vop: {analysis.nodes['Vop'][0]:.4f} V")
        except Exception as e:
            # If it fails, we finally look at the internal Ngspice error buffer
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            # Access the shared instance to see what went wrong inside
            # print(NgSpiceShared.get_instance().stdout)
            print(e)
            raise e

        iq = float(analysis.branches['vVDD'][0])
        Vop = float(analysis.nodes['Vop'][0])

        print(f"\n--- OPERATING POINT RESULTS ---")
        print(f"Node 'Vop'  : {Vop:.4f} V")
        print(f"I-Quiescent : {abs(iq)*1e6:.2f} uA")

    elif mode == 'TRANS':
        circuit.V('vpp', 'Vpp', circuit.gnd, 'SIN(0.9V 1mV 100Hz)') 
        circuit.V('vpn', 'Vpn', circuit.gnd, 'SIN(0.9V -1mV 100Hz)')
        circuit.V('vnn', 'Vnn', circuit.gnd, 'dc 0.9')
        circuit.V('vnp', 'Vnp', circuit.gnd, 'dc 0.9')
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
        circuit.V('input_p', 'Vpp', circuit.gnd, 'PULSE(0.9V 1.1V 150n 1n 1n 2500n 5000n)')
        circuit.V('input_n', 'Vnn', circuit.gnd, 'PULSE(0.9V 0.7V 150n 1n 1n 2500n 5000n)')
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
    'W_1': 1, 'L_1': 1, 'nf_1': 1, 'm_1': 88,
    'W_2': 1, 'L_2': 1, 'nf_2': 1, 'm_2': 88,
    'W_3': 1, 'L_3': 1, 'nf_3': 1, 'm_3': 88,
    'W_4': 1, 'L_4': 1, 'nf_4': 1, 'm_4': 14,
    'W_5': 1, 'L_5': 1, 'nf_5': 1, 'm_5': 28,
    'W_6': 1, 'L_6': 1, 'nf_6': 1, 'm_6': 176,
}

generate_spice_file(params)

run_simulation('AC')
# run_simulation('OP')
# run_simulation('TRANS')
# run_simulation('SLEW')



