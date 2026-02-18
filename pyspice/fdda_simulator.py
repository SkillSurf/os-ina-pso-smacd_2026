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
    """Generates hard-coded .spice files to avoid parameter parsing errors."""
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
Vmeas1 net11 net1 0V
Vmeas2 net5 net9 0V
Vmeas3 net6 net10 0V
Vmeas4 net12 net2 0V
Vmeas5 net13 net9 0V
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
XMP11 net11 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_6']} {g_6} sa=0 sb=0 sd=0
+ mult=1 m=1
XMP12 net12 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_6']} {g_6} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN3 Von Vb3 net13 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN4 Vop Vb3 net6 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN9 net9 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0
+ mult=1 m=1
XMN10 net10 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0
+ mult=1 m=1

.ends
"""
    with open('fdda.spice', 'w') as f:
        f.write(content)

def generate_cmfb(params):
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
    g_4  = get_geom_string(params['W_4'], params['nf_4'])
    g_5  = get_geom_string(params['W_5'], params['nf_5'])
    g_6  = get_geom_string(params['W_6'], params['nf_6'])

    content=f"""*CMFB auto generated
.subckt CMFB VDD Vop Von Vcm Vb2 Vcmfb

XMP9 n1 n1 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
XMP10 n2 n2 VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_1']} {g_1} sa=0 sb=0 sd=0
XMP13 Vcmfb Vcmfb VDD VDD sky130_fd_pr__pfet_01v8 L={params['L_6']} {g_6} sa=0 sb=0 sd=0
XMN1 n1 Vop  nt1 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
XMN2 Vcmfb Vcm  nt1 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
XMN5 Vcmfb Vcm  nt2 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
XMN6 n2 Von  nt2 0 sky130_fd_pr__nfet_01v8 L={params['L_4']} {g_4} sa=0 sb=0 sd=0
XMN7 nt1 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0
XMN8 nt2 Vb2 0 0 sky130_fd_pr__nfet_01v8 L={params['L_5']} {g_5} sa=0 sb=0 sd=0

.ends CMFB

"""
    with open('cmfb.spice', 'w') as f:
        f.write(content)

def generate_bias():

    content=f"""*Bias circuit auto generated
.subckt BIAS VDD Vb1 Vb2 Vb3 Vb4

IREF VDD n1 2.5uA
XMN11 n1 n1 0 0 sky130_fd_pr__nfet_01v8 L=2 W=5
XMN12 Vb1 n1 0 0 sky130_fd_pr__nfet_01v8 L=2 W=5

XMP14 Vb1 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L=2 W=35
XMP15 Vb3 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L=2 W=35
XMP16 Vb2 Vb1 VDD VDD sky130_fd_pr__pfet_01v8 L=2 W=35
XMP17 Vb4 Vb4 VDD VDD sky130_fd_pr__pfet_01v8 L=3 W=5

XMN13 Vb3 Vb3 0 0 sky130_fd_pr__nfet_01v8 L=4 W=1
XMN14 Vb2 Vb2 0 0 sky130_fd_pr__nfet_01v8 L=2 W=5
XMN15 Vb4 Vb2 0 0 sky130_fd_pr__nfet_01v8 L=2 W=5

.ends BIAS
"""

    with open('bias.spice', 'w') as f:
        f.write(content)


#Main simulation code
def run_simulation(mode):

    circuit = Circuit('FDDA Simulation')
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
.lib /foss/pdks/sky130A/libs.tech/ngspice/sky130.lib.spice tt
.include /foss/designs/os-ina-pso-mixdes_2026/pyspice/fdda.spice
.include /foss/designs/os-ina-pso-mixdes_2026/pyspice/cmfb.spice
.include /foss/designs/os-ina-pso-mixdes_2026/pyspice/bias.spice

"""

    circuit.X('X1', 'FDDA', 'VDD', 'Vpp', 'Vpn', 'Vnp', 'Vnn', 'Vcmfb', 'Vb1', 'Vb2', 'Vb3', 'Vb4', 'Von', 'Vop')
    circuit.X('X2', 'CMFB', 'VDD', 'Vop', 'Von', 'Vcm', 'Vb2', 'Vcmfb')
    circuit.X('X3', 'BIAS', 'VDD', 'Vb1', 'Vb2', 'Vb3', 'Vb4')
    
    circuit.V('vdd', 'VDD', circuit.gnd, 1.8@u_V)
    circuit.V('vcm', 'Vcm', circuit.gnd, 0.9@u_V)
    
    circuit.C('load_p', 'Vop', circuit.gnd, 0.5@u_pF)
    circuit.C('load_n', 'Von', circuit.gnd, 0.5@u_pF)
    


    if mode == 'AC':        # Define AC Input (Differential)
        circuit.V('vpp', 'Vpp', circuit.gnd, 'dc 0 ac 0.5')
        circuit.V('vpn', 'Vpn', circuit.gnd, 'dc 0 ac -0.5')
        circuit.V('vnp', 'Vnp', circuit.gnd, 'dc 0 ac -0.5')
        circuit.V('vnn', 'Vnn', circuit.gnd, 'dc 0 ac 0.5')

        simulator = circuit.simulator(simulator='ngspice-subprocess', temperature=25)

        try:
            analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        except Exception as e:
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            print(e)
            raise e

        op_analysis = simulator.operating_point()

        # Check DC levels before looking at AC results
        print(f"DC Vop: {float(op_analysis.nodes['Vop'][0]):.3f} V")
        print(f"DC Von: {float(op_analysis.nodes['Von'][0]):.3f} V")
        print(f"DC Vcmfb: {float(op_analysis.nodes['Vcmfb'][0]):.3f} V")
        print(f"net1: {float(op_analysis.nodes['xx1.net1'][0]):.3f} V")
        print(f"net2: {float(op_analysis.nodes['xx1.net2'][0]):.3f} V")
        print(f"Vb1: {float(op_analysis.nodes['Vb1'][0]):.3f} V")
        print(f"Vb2: {float(op_analysis.nodes['Vb2'][0]):.3f} V")
        print(f"Vb3: {float(op_analysis.nodes['Vb3'][0]):.3f} V")
        print(f"Vb4: {float(op_analysis.nodes['Vb4'][0]):.3f} V")

        print(f"Current net11: {float(op_analysis.branches['v.xx1.vmeas1'][0])*1e6:.3f} uA")
        print(f"Current net12: {float(op_analysis.branches['v.xx1.vmeas4'][0])*1e6:.3f} uA")
        print(f"Current net13: {float(op_analysis.branches['v.xx1.vmeas5'][0])*1e6:.3f} uA")
        print(f"Current net5: {float(op_analysis.branches['v.xx1.vmeas2'][0])*1e6:.3f} uA")
        print(f"Current net6: {float(op_analysis.branches['v.xx1.vmeas3'][0])*1e6:.3f} uA")

        #write all the node voltage values to a file
        with open('simulation_results.txt', 'w') as f:
            f.write("--- NODE VOLTAGES AT START FREQUENCY ---\n")
            f.write(f"{'Node Name':<20} | {'Voltage (V)':<10}\n")
            f.write("-" * 35 + "\n")

            for node_name in op_analysis.nodes:
                voltage_complex = op_analysis.nodes[node_name][0]
                magnitude = float(np.abs(voltage_complex))
                f.write(f"{node_name:<20} | {magnitude:.6f} V\n")

        # AC analysis - open loop DC gain, GBW, PM
        freq = np.array(analysis.frequency)
        vout = analysis.nodes['Vop'] - analysis.nodes['Von']
        vin  = (analysis.nodes['Vpp'] - analysis.nodes['Vpn'])-(analysis.nodes['Vnp'] - analysis.nodes['Vnn'])

        gain = vout / vin
        gain_db = 20*np.log10(np.abs(gain))
        phase_deg = np.angle(gain, deg=True)

        dc_gain = gain_db[0]
        gbw = np.interp(0, gain_db[::-1], freq[::-1])
        phase_at_gbw = np.interp(gbw, freq, phase_deg)
        phase_margin = 180 + phase_at_gbw

        # Performing the CMRR A_CM calculation
        for name in ['Vvpp', 'Vvpn', 'Vvnp', 'Vvnn']:
            circuit._elements.pop(name)

        circuit.V('vpp', 'Vpp', circuit.gnd, 'dc 0 ac 1')
        circuit.V('vpn', 'Vpn', circuit.gnd, 'dc 0 ac 1')
        circuit.V('vnp', 'Vnp', circuit.gnd, 'dc 0 ac 1')
        circuit.V('vnn', 'Vnn', circuit.gnd, 'dc 0 ac 1')

        simulator = circuit.simulator(simulator='ngspice-subprocess', temperature=25)

        try:
            analysis = simulator.ac(start_frequency=1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        except Exception as e:
            print("\n--- NGSPICE ERROR LOG ---")
            print(str(simulator))
            print(e)
            raise e

        vout_cm = analysis.nodes['Vop'] - analysis.nodes['Von']
        vin_cm  = (analysis.nodes['Vpp'] + analysis.nodes['Vpn'] + analysis.nodes['Vnp'] + analysis.nodes['Vnn'])/4

        gain_cm = vout_cm / vin_cm
        # gain_cm = vout_cm
        gain_cm_db = 20 * np.log10(np.abs(gain_cm))

        cmrr_db = gain_db - gain_cm_db

        # finding the gain at the target freq of 1kHz
        target_freq = 1000  # 1kHz
        idx = (np.abs(freq - target_freq)).argmin()

        ad_1k = (gain_db[idx])
        acm_1k = (gain_cm_db[idx])
        print(f"Calculated AC Gain @1kHz: {ad_1k:.2f} dB")
        print(f"Calculated CM Gain @1kHz: {acm_1k:.2f} dB")

        cmrr = ad_1k - acm_1k

        print(f"\n--- AC ANALYSIS RESULTS ---")
        print(f"Calculated DC Gain: {dc_gain:.2f} dB | Calculated GBW: {gbw/1e6:.2f} MHz | Calculated PM: {phase_margin:.2f} degrees")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.semilogx(freq, gain_db, color='blue', marker='.', linestyle='-')
        ax1.set_ylabel('Gain (dB)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("Bode Diagram of Biomedical INA")

        ax2.semilogx(freq, phase_deg, color='green', marker='.', linestyle='-')
        ax2.set_ylabel('phase (degree)')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.grid(True, which="both", ls="-")

        ax1.axhline(y=0, color='red', linestyle='--')
        ax2.axhline(y=0, color='red', linestyle='--')  

        plt.savefig('Gain_and_GBW_plot.png')
        plt.tight_layout()
        # plt.show()

        fig, ax1 = plt.subplots(figsize=(12, 8))
                
        l1 = ax1.semilogx(freq, gain_db, label='Gain', color='red', linewidth=2)
        l2 = ax1.semilogx(freq, cmrr_db, label='CMRR', color='green', linestyle='--')
        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("Magnitude (dB)", color='black')
        ax1.grid(True, which="both", ls="-", alpha=0.5)

        ax2 = ax1.twinx() 
        l3 = ax2.semilogx(freq, phase_deg, label='Phase', color='blue', linestyle='-.')
        ax2.set_ylabel("Phase (Degrees)", color='blue')
                
        lns = l1 + l2 + l3
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc='center right')

        plt.title("Frequency response plot with Gain, Phase, CMRR for the FDDA circuit")
        plt.tight_layout()
        plt.savefig('Frequency_response.png')
        # plt.show()

        specs = {
            "Open-loop gain": {"val": dc_gain, "target": 70, "unit": "dB", "op": ">="},
            "GBW": {"val": gbw/1e6, "target": 30, "unit": "MHz", "op": ">="},
            "Phase Margin": {"val": phase_margin, "target": 60, "unit": "deg", "op": ">"},
            "CMRR": {"val": cmrr, "target": 120, "unit": "db", "op": ">"}
                    # "Power Total": {"val": power_uw, "target": 500, "unit": "uW", "op": "<="}
        }

        print(f"\n--- Results ---")
        all_passed = True

        for key, s in specs.items():
            passed = (s['val'] >= s['target']) if s['op'] == ">=" else (s['val'] <= s['target'])
            if s['op'] == ">": passed = s['val'] > s['target']
                    
            status = "PASS" if passed else "FAIL"
            if not passed: all_passed = False
            print(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}")

            with open('specs_comparison.txt', 'a') as f:
                f.write(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}\n")

        return all_passed


    elif mode == 'TRANS':
        circuit.V('vpp', 'Vpp', circuit.gnd, 'SIN(0.9V 10mV 100Hz)') 
        circuit.V('vpn', 'Vpn', circuit.gnd, 'SIN(0.9V -10mV 100Hz)')
        
        circuit.V('vnp', 'Vnp', circuit.gnd, '0.9V')
        circuit.V('vnn', 'Vnn', circuit.gnd, '0.9V')

        simulator = circuit.simulator(simulator='ngspice-subprocess')
        analysis = simulator.transient(step_time=50@u_us, end_time=30@u_ms)

        time = np.array(analysis.time)
        vop = np.array(analysis.nodes['Vop'])
        von = np.array(analysis.nodes['Von'])
        vpp = np.array(analysis.nodes['Vpp'])
        vpn = np.array(analysis.nodes['Vpn'])
        
        v_out_diff = vop - von
        v_in_diff = vpp - vpn

        print(f"\n--- TRANSIENT ANALYSIS ---")
        plt.figure(figsize=(10, 6))
        
        # Plot Differential Output and Input
        plt.plot(time * 1e3, v_out_diff, label='Differential Output (Vop-Von)', color='blue')
        plt.plot(time * 1e3, v_in_diff, label='Differential Input (Vpp-Vpn)', color='red', linestyle='--')
        
        plt.xlabel("Time (ms)")
        plt.ylabel("Voltage (V)")
        plt.legend()
        plt.title("FDDA Transient Response: 100Hz Differential Sine Wave")
        plt.grid(True)
        plt.savefig('Transient_analysis.png')
        # plt.show()

    elif mode == 'SLEW':
        circuit.V('vpp', 'Vpp', circuit.gnd, 'PULSE(0.9 1.5 10u 10n 10n 20u 40u)')
        circuit.V('vpn', 'Vpn', circuit.gnd, 'PULSE(0.9 0.3 10u 10n 10n 20u 40u)') 
        circuit.R('f1', 'Vop', 'Vnp', 1000@u_Ohm)
        circuit.R('f2', 'Von', 'Vnn', 1000@u_Ohm)
        circuit.C('L1', 'Vop', circuit.gnd, 1@u_pF)
        circuit.C('L2', 'Von', circuit.gnd, 1@u_pF)

        simulator = circuit.simulator(simulator='ngspice-subprocess')
        simulator.options('rshunt=1e12', 'method=gear', 'abstol=1e-12') # More stable for fast transitions
        analysis = simulator.transient(step_time=1@u_ns, end_time=50@u_us, max_time=10@u_ns)
        
        time = np.array(analysis.time).astype(float)
        vout = np.array(analysis.nodes['Vop']) - np.array(analysis.nodes['Von'])
        vin  = np.array(analysis.nodes['Vpp']) - np.array(analysis.nodes['Vpn'])

        mask = (time >= 9e-6) & (time <= 10.5e-6)
        time_zoom = time[mask]
        vout_zoom = vout[mask]
        vin_zoom = vin[mask]

        vop = np.array(analysis.nodes['Vop'])
        von = np.array(analysis.nodes['Von'])
        vpp = np.array(analysis.nodes['Vpp'])
        vpn = np.array(analysis.nodes['Vpn'])
        vnp = np.array(analysis.nodes['Vnp'])
        vnn = np.array(analysis.nodes['Vnn'])
        vcmfb = np.array(analysis.nodes['Vcmfb'])

        print("Vop DC:", float(vop[0]))
        print("Von DC:", float(von[0]))
        print("Vpp DC:", float(vpp[0]))
        print("Vpn DC:", float(vpn[0]))
        print("Vnp DC:", float(vnp[0]))
        print("Vnn DC:", float(vnn[0]))
        print("Vcmfb DC:", float(vcmfb[0]))
        print("Vout:", vout_zoom)
        print("Vin:", vin_zoom)

        try:
            v_min = np.min(vout_zoom)
            v_max = np.max(vout_zoom)
            v_swing = v_max - v_min
            
            target_v_10 = v_min + (0.10 * v_swing)
            target_v_90 = v_min + (0.90 * v_swing)

            idx_10 = np.where(vout_zoom >= target_v_10)[0][0]
            idx_90 = np.where(vout_zoom >= target_v_90)[0][0]
            print("idx_10:", idx_10)
            print("idx_90:", idx_90)
            
            t_10, t_90 = time_zoom[idx_10], time_zoom[idx_90]
            v_actual_10, v_actual_90 = vout_zoom[idx_10], vout_zoom[idx_90]
            print("t_10:", t_10)
            print("t_90:", t_90)
            print("vactual_10:", v_actual_10)
            print("vactual_90:", v_actual_90)

            # 4. Calculate Slew Rate
            slew = (v_actual_90 - v_actual_10) / (t_90 - t_10)
            slew_us = slew / 1e6  # V/us
            print(f"Measured Slew Rate: {slew_us:.2f} V/us")
        except IndexError:
            slew_us = 0
            print("Error: The output didn't reach the 10%/90% thresholds. Check your gain/bias.")

        
        print(f"\n--- SLEW RATE ---")
        print(f"Measured Slew Rate: {slew_us:.2f} V/us")
        

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.plot(time_zoom * 1e6, vin_zoom, color='blue', linestyle='-')
        ax1.set_ylabel('Input Voltage (V)')
        ax1.grid(True, which="both", ls="-")
        ax1.set_title("Slew Response (positive closed loop)")

        ax2.plot(time_zoom * 1e6, vout_zoom, color='blue', linestyle='-')
        ax2.set_ylabel('Output Voltage (V)')
        ax2.set_xlabel('Time (s)')
        ax2.grid(True, which="both", ls="-")

        if slew_us > 0:
            ax2.scatter([t_10*1e6, t_90*1e6], [v_actual_10, v_actual_90], color='black', zorder=5)

        plt.xlim(9.5, 10.5)
        plt.tight_layout()
        plt.savefig('Slewrate_positive_closedloop.png')
        # plt.show()

        all_passed = True

        specs = {
            "Slewrate": {"val": slew_us, "target": 1, "unit": "V/us", "op": ">"}
        }

        for key, s in specs.items():
            passed = (s['val'] >= s['target']) if s['op'] == ">=" else (s['val'] <= s['target'])
            if s['op'] == ">": passed = s['val'] > s['target']
                    
            status = "PASS" if passed else "FAIL"
            if not passed: all_passed = False
            print(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}")

            with open('specs_comparison.txt', 'a') as f:
                f.write(f"{key}: {s['val']:.2f}{s['unit']} (Target: {s['op']}{s['target']}) -> {status}\n")

        return all_passed
        

params = {
    'W_1': 88, 'L_1': 1, 'nf_1': 1, 'm_1': 1,
    'W_2': 88, 'L_2': 1, 'nf_2': 1, 'm_2': 1,
    'W_3': 88, 'L_3': 1, 'nf_3': 1, 'm_3': 1,
    'W_4': 14, 'L_4': 1, 'nf_4': 1, 'm_4': 1,
    'W_5': 28, 'L_5': 1, 'nf_5': 1, 'm_5': 1,
    'W_6': 88, 'L_6': 1, 'nf_6': 1, 'm_6': 2,
}

generate_spice_file(params)
generate_cmfb(params)
generate_bias()

run_simulation('AC')
run_simulation('TRANS')
run_simulation('SLEW')

