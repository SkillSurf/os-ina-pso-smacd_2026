from gmID_sizing import *
from specs import *
from survivability_check import survivability_test
import numpy as np
from simulator import evaluate_design

if __name__ == "__main__":
    # Example particle
    particle = np.array([19.1743, 14.2497, 12.1117, 12.5996, 12.0605, 11.0269, 6, 15, 8, 15, 14, 8, 15, 4.4422e-6])
    
    passed, area, specs = survivability_test(particle)
    
    if passed:
        print(f"\nArea: {area:.2f} μm²")

        print("\n--- Performance Calculations ---")
        if 'Gain_dB' in specs: print(f"  Gain_dB: {specs['Gain_dB']:.2f} dB")
        if 'GBW' in specs:     print(f"  GBW:     {specs['GBW'] / 1e6:.2f} MHz")
        if 'PM' in specs:      print(f"  PM:      {specs['PM']:.2f} °")
        if 'SR' in specs:      print(f"  SR:      {specs['SR'] / 1e6:.2f} V/µs")
        if 'Power' in specs:   print(f"  Power:   {specs['Power'] * 1e6:.2f} µW")
        if 'V_CMFB' in specs:  print(f"  V_CMFB:  {specs['V_CMFB']:.4f} V")

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

        print("\n--- Performance Measurements ---")
        if 'Gain_dB' in meas: print(f"  Gain_dB: {meas['Gain_dB']:.2f} dB")
        if 'GBW' in meas:     print(f"  GBW:     {meas['GBW'] / 1e6:.2f} MHz")
        if 'PM' in meas:      print(f"  PM:      {meas['PM']:.2f} °")
        if 'SR' in meas:      print(f"  SR:      {meas['SR'] / 1e6:.2f} V/µs")
        if 'Power' in meas:   print(f"  Power:   {meas['Power'] * 1e6:.2f} µW")
        if 'V_CMFB' in meas:  print(f"  V_CMFB:  {meas['V_CMFB']:.4f} V")
        if 'CMRR_dB' in meas: print(f"  CMRR_dB: {meas['CMRR_dB']:.2f} dB")
        if 'PSRR_dB' in meas: print(f"  PSRR_dB: {meas['PSRR_dB']:.2f} dB")

        print("\n--- Transistor Dimensions ---")
        # Loops from 1 through 8 to catch all your W and L pairs
        for i in range(1, 9):
            w_key, l_key = f"W_{i}", f"L_{i}"
            if w_key in meas and l_key in meas:
                # Pads the string for clean alignment
                print(f"  W_{i} = {meas[w_key]:<6.2f} μm,  L_{i} = {meas[l_key]:.2f} μm")

        print("\n--- Bias Voltages ---")
        # Loops from 1 through 4 to catch all your V_B nodes
        for i in range(1, 5):
            v_key = f"V_B{i}"
            if v_key in meas:
                print(f"  {v_key}: {meas[v_key]:.4f} V")
    else:
        print("Particle does NOT meet specifications.\n")
        print(specs)