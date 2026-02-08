import numpy as np

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

from params import *
from specs import *

logger = Logging.setup_logging()

params = {'W_1': W_1, 'L_1': L_1, 'W_2': W_2, 'L_2': L_2, 'ID': ID}
measurement_results = {}

##############################################################
# Generates a hard-coded SPICE file in OPEN-LOOP configuration
##############################################################
def generate_spice(params):

    # Extract parameters
    W_1 = params['W_1']
    L_1 = params['L_1']
    W_2 = params['W_2']
    L_2 = params['L_2']
    IDD = 2 * params['ID']

    # Generate the SPICE content with the extracted parameters
    content = f"""* 5T_OTA (Auto-generated)
.subckt 5T_OTA VDD Vout Vin Vip VSS
XM1 Vx Vip Vc Vc sky130_fd_pr__nfet_01v8 L={L_1} W={W_1} nf=1 ad='int((1 + 1)/2) * {W_1} / 1 * 0.29' as='int((1 + 2)/2) * {W_1} / 1 * 0.29'
+ pd='2*int((1 + 1)/2) * ({W_1} / 1 + 0.29)' ps='2*int((1 + 2)/2) * ({W_1} / 1 + 0.29)' nrd='0.29 / {W_1} ' nrs='0.29 / {W_1} ' sa=0
+ sb=0 sd=0 mult=1 m=1
XM2 Vout Vin Vc Vc sky130_fd_pr__nfet_01v8 L={L_1} W={W_1} nf=1 ad='int((1 + 1)/2) * {W_1} / 1 * 0.29' as='int((1 + 2)/2) * {W_1} / 1 * 0.29'
+ pd='2*int((1 + 1)/2) * ({W_1} / 1 + 0.29)' ps='2*int((1 + 2)/2) * ({W_1} / 1 + 0.29)' nrd='0.29 / {W_1} ' nrs='0.29 / {W_1} ' sa=0
+ sb=0 sd=0 mult=1 m=1
I0 Vc VSS {IDD}u
XM3 Vx Vx VDD VDD sky130_fd_pr__pfet_01v8 L={L_2} W={W_2} nf=1 ad='int((1 + 1)/2) * {W_2} / 1 * 0.29' as='int((1 + 2)/2) * {W_2} / 1 * 0.29'
+ pd='2*int((1 + 1)/2) * ({W_2} / 1 + 0.29)' ps='2*int((1 + 2)/2) * ({W_2} / 1 + 0.29)' nrd='0.29 / {W_2} ' nrs='0.29 / {W_2} ' sa=0
+ sb=0 sd=0 mult=1 m=1
XM4 Vout Vx VDD VDD sky130_fd_pr__pfet_01v8 L={L_2} W={W_2} nf=1 ad='int((1 + 1)/2) * {W_2} / 1 * 0.29' as='int((1 + 2)/2) * {W_2} / 1 * 0.29'
+ pd='2*int((1 + 1)/2) * ({W_2} / 1 + 0.29)' ps='2*int((1 + 2)/2) * ({W_2} / 1 + 0.29)' nrd='0.29 / {W_2} ' nrs='0.29 / {W_2} ' sa=0
+ sb=0 sd=0 mult=1 m=1
.ends
"""
    with open('5t_ota.spice', 'w') as f:
        f.write(content)

######################################################
# Runs the specified simulation mode (AC, OP, or SLEW)
######################################################
def run_simulation(mode, measurement_results=measurement_results):

    circuit = Circuit('5T_OTA Simulation')
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
.lib ../../../../PDKs/sky130A/libs.tech/combined/sky130.lib.spice tt
.include 5t_ota.spice
"""

    circuit.X('X1', '5T_OTA', 'VDD', 'Vout', 'Vin', 'Vip', circuit.gnd)
    circuit.V('vdd', 'VDD', circuit.gnd, 1.8@u_V)
    circuit.C('load_p', 'Vout', circuit.gnd, 2@u_pF)

    if mode == 'AC':
        # Define AC Input (Differential)
        circuit.V('vip', 'Vip', circuit.gnd, 'DC 0.9 AC 0.5')
        circuit.V('vin', 'Vin', circuit.gnd, 'DC 0.9 AC -0.5')

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)

        try:
            analysis = simulator.ac(start_frequency=0.1@u_Hz, stop_frequency=100@u_MHz, number_of_points=20, variation='dec')
        except Exception as e:
            print("--------------------------------")
            print("REAL NGSPICE ERROR:")
            # This grabs the internal log from the shared library
            print(simulator.ngspice.stdout) 
            print(simulator.ngspice.stderr)
            print("--------------------------------")
            raise e

        freq = np.array(analysis.frequency)
        vout = analysis.nodes['vout']
        vin  = (analysis.nodes['vip'] - analysis.nodes['vin'])

        gain = vout / vin
        gain_db = 20 * np.log10(np.abs(gain))
        phase_deg = np.angle(gain, deg=True)

        dc_gain = float(gain_db[0])
        gbw = float(np.interp(0, gain_db[::-1], freq[::-1]))
        phase_at_gbw = float(np.interp(gbw, freq, phase_deg))
        phase_margin = 180 + phase_at_gbw

        measurement_results['Gain_meas_dB'] = dc_gain
        measurement_results['GBW_meas'] = gbw
        measurement_results['PM_meas'] = phase_margin

    if mode == 'OP':
        # Define DC Inputs (Quiescent Points)
        circuit.V('vip', 'Vip', circuit.gnd, 'DC 0.9')
        circuit.V('vin', 'Vin', circuit.gnd, 'DC 0.9')

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)

        try:
            analysis = simulator.operating_point()
        except Exception as e:
            print("--------------------------------")
            print("REAL NGSPICE ERROR:")
            # This grabs the internal log from the shared library
            print(simulator.ngspice.stdout) 
            print(simulator.ngspice.stderr)
            print("--------------------------------")
            raise e

        iq = float(analysis.branches['vvdd'][0])
        power = abs(iq) * 1.8

        measurement_results['Power_meas'] = power

    if mode == 'SLEW':
        # Form the closed-loop configuration by connecting Vout to Vin (Unity gain)
        circuit.V('vin', 'Vin', 'Vout', 0@u_V)
        # Define Pulse Input on Vip (Single-ended)
        circuit.V('vip', 'Vip', circuit.gnd, 'DC 0 PULSE(0 1.8 10u 10p 10p 20u 40u)')

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)

        try:
            analysis = simulator.transient(step_time=10@u_ns, end_time=20@u_us)
        except Exception as e:
            print("--------------------------------")
            print("REAL NGSPICE ERROR:")
            # This grabs the internal log from the shared library
            print(simulator.ngspice.stdout) 
            print(simulator.ngspice.stderr)
            print("--------------------------------")
            raise e

        time = np.array(analysis.time)
        vout = analysis.nodes['vout']

        v_min = np.min(vout)
        v_max = np.max(vout)

        v_swing = float(v_max) - float(v_min)
        v_10 = float(v_min) + (0.1 * v_swing)
        v_90 = float(v_max) - (0.1 * v_swing)

        t_10 = np.interp(v_10, vout, time)
        t_90 = np.interp(v_90, vout, time)

        slew = float((v_90 - v_10) / (t_90 - t_10))

        measurement_results['SR_meas'] = slew

        return None

###################################################
# Return TRUE if all specs are met, otherwise FALSE
###################################################
def check_specs(measurement_results):
    specs_met = (measurement_results['Gain_meas_dB'] >= Gain_spec_dB and
                 measurement_results['GBW_meas'] >= GBW_spec and
                 measurement_results['PM_meas'] >= PM_spec and
                 measurement_results['Power_meas'] <= Power_spec)

    return specs_met

generate_spice(params)
run_simulation('AC')
run_simulation('OP')
run_simulation('SLEW')

specs_met = check_specs(measurement_results)
print(measurement_results)