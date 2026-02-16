import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator

import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

from specs import *

logger = Logging.setup_logging(logging_level='CRITICAL')

##############################################################
# Generates a hard-coded SPICE file in OPEN-LOOP configuration
##############################################################
def generate_spice(params):

    # Read the SPICE template file
    with open('ref.spice', 'r') as f:
        template = f.read()

    # Inject the parameters into the placeholders in the SPICE template
    spice = template.format(
    # Extract parameters
    W_1 = params['W_1'],
    L_1 = params['L_1'],
    W_2 = params['W_2'],
    L_2 = params['L_2'],
    IDD = 2 * params['ID'],
    Template = 'Auto-Generated'
    )

    # Generate the SPICE content with the extracted parameters
    with open('5t_ota.spice', 'w') as f:
        f.write(spice)

######################################################
# Runs the specified simulation mode (AC, OP, or SLEW)
######################################################
def run_simulation(mode, measurement_results, plots=False):

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


        if plots:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            ax1.semilogx(freq, gain_db, color='blue', linestyle='-')
            ax1.set_ylabel('Gain (dB)')
            ax1.grid(True, which="both", ls="-")
            ax1.set_title("Bode Plot of 5T-OTA")

            ax2.semilogx(freq, phase_deg, color='blue', linestyle='-')
            ax2.set_ylabel('Phase (Degrees)')
            ax2.set_xlabel('Frequency (Hz)')
            ax2.grid(True, which="both", ls="-")
            locator = LogLocator(base=10.0, numticks=15)
            ax2.xaxis.set_major_locator(locator)

            ax1.axhline(y=0, color='red', linestyle='--') 
            ax2.axhline(y=-180, color='red', linestyle='--') 

            plt.savefig('Gain_and_GBW_plot.png')
            plt.tight_layout()

    if mode == 'OP':
        # Define DC Inputs (Quiescent Points)
        circuit.V('vip', 'Vip', circuit.gnd, 'DC 0.9')
        circuit.V('vin', 'Vin', circuit.gnd, 'DC 0.9')

        simulator = circuit.simulator(temperature=25, nominal_temperature=25)

        try:
            analysis = simulator.operating_point()
        except Exception as e:
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

        if plots:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            ax1.plot(time, analysis.nodes['vip'], color='blue', linestyle='-')
            ax1.set_ylabel('Input Voltage (V)')
            ax1.grid(True, which="both", ls="-")
            ax1.set_title("5T-OTA Slew Response")

            ax2.plot(time, vout, color='blue', linestyle='-')
            ax2.set_ylabel('Output Voltage (V)')
            ax2.set_xlabel('Time (s)')
            ax2.grid(True, which="both", ls="-")

            plt.savefig('Slew_plot.png')
            plt.tight_layout()

        return None

###################################################
# Return TRUE if all specs are met, otherwise FALSE
###################################################
def check_specs(measurement_results):
    specs_met = (measurement_results['Gain_meas_dB'] >= Gain_spec_dB and
                 measurement_results['GBW_meas'] >= GBW_spec and
                 measurement_results['PM_meas'] >= PM_spec and
                 measurement_results['Power_meas'] <= Power_spec and
                 measurement_results['SR_meas'] >= SR_spec)

    return specs_met

#############################################################
# Top-level function to evaluate a design given the variables
#############################################################
def evaluate_design(W_1, L_1, W_2, L_2, ID, plots=False):
    """
    Accepts the 5 generated variables, runs the simulation, 
    and returns the binary result.
    """
    
    # Pack inputs into the dictionary
    current_params = {'W_1': W_1, 'L_1': L_1, 'W_2': W_2, 'L_2': L_2, 'ID': ID}
    # Round all parameters to 2 decimal places
    rounded_params = {k: round(v, 2) for k, v in current_params.items()}
    
    # Create a new results dictionary for this specific run
    current_results = {}

    # Run the sequence
    try:
        generate_spice(rounded_params)
        
        # Pass the local 'current_results' dict to your simulation functions
        run_simulation('AC', measurement_results=current_results, plots=plots)
        run_simulation('OP', measurement_results=current_results, plots=plots)
        run_simulation('SLEW', measurement_results=current_results, plots=plots)
        
        # Check specs and return result
        specs_met = check_specs(current_results)
        return specs_met, current_results
        
    except Exception as e:  # Simulation failed for params
        return False, None # Return as an infeasible solution