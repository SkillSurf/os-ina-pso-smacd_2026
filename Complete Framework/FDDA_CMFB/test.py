from gmID_sizing import *
from specs import *
from survivability_check import survivability_test
import numpy as np
from simulator import evaluate_design

if __name__ == "__main__":
    # Example particle
    particle = np.array([18, 15, 15, 15, 15, 15, 13, 13, 13, 13, 13, 13, 5e-6, 1.5, 0.3])
    
    passed, area, specs = survivability_test(particle)
    
    if passed:
        print("Particle meets all specifications!")
        print(f"Area: {area:.2e} m^2")
        print("Specifications:")
        for spec_name, spec_value in specs.items():
            print(f"  {spec_name}: {spec_value:.2e}")

        current_params = {
                'W_1': specs['W_1'], 'L_1': specs['L_1'],
                'W_2': specs['W_2'], 'L_2': specs['L_2'],
                'W_3': specs['W_3'], 'L_3': specs['L_3'],
                'W_4': specs['W_4'], 'L_4': specs['L_4'],
                'W_5': specs['W_5'], 'L_5': specs['L_5'],
                'W_6': specs['W_6'], 'L_6': specs['L_6'],
                'W_7': specs['W_7'], 'L_7': specs['L_7'],
                'W_8': specs['W_8'], 'L_8': specs['L_8'],
                'V_B1': specs['V_B1'],
                'V_B2': specs['V_B2'],
                'V_B3': specs['V_B3'],
                'V_B4': specs['V_B4'],
                'V_CM': VCM
            }            
        sim_passed, meas = evaluate_design(current_params)
        print("\nSimulation Results:")
        for meas_name, meas_value in meas.items():
            print(f"  {meas_name}: {meas_value:.2e}")
    else:
        print("Particle does NOT meet specifications.\n")