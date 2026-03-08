import numpy as np
from simulator import evaluate_design
from survivability_check import survivability_test
from specs import L_DISCRETE_VALUES, VDD, VCM, V_A, V_B

def generate_particle(cont_bounds, n_L_values, max_attempts=2000):

    for attempt in range(max_attempts):
        gm_ID_1 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_2 = np.random.uniform(cont_bounds[1][0], cont_bounds[1][1])
        gm_ID_3 = np.random.uniform(cont_bounds[2][0], cont_bounds[2][1])
        gm_ID_4 = np.random.uniform(cont_bounds[3][0], cont_bounds[3][1])
        gm_ID_5 = np.random.uniform(cont_bounds[4][0], cont_bounds[4][1])
        gm_ID_6 = np.random.uniform(cont_bounds[5][0], cont_bounds[5][1])
        
        L_1_idx = np.random.randint(0, n_L_values)
        L_2_idx = np.random.randint(0, n_L_values)
        L_3_idx = np.random.randint(0, n_L_values)
        L_4_idx = np.random.randint(0, n_L_values)
        L_5_idx = np.random.randint(0, n_L_values)
        L_6_idx = np.random.randint(0, n_L_values)

        I_T = np.random.uniform(cont_bounds[6][0], cont_bounds[6][1])
        
        particle = np.array([gm_ID_1, gm_ID_2, gm_ID_3, gm_ID_4, gm_ID_5, gm_ID_6, 
                             L_1_idx, L_2_idx, L_3_idx, L_4_idx, L_5_idx, L_6_idx, I_T])
        
        passed, area, specs = survivability_test(particle)
        
        if passed:
            return particle, area, specs
    
    return None, np.inf, None

def generate_initial_particle(cont_bounds, n_L_values, max_attempts=100000):

    for attempt in range(max_attempts):
        gm_ID_1 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_2 = np.random.uniform(cont_bounds[1][0], cont_bounds[1][1])
        gm_ID_3 = np.random.uniform(cont_bounds[2][0], cont_bounds[2][1])
        gm_ID_4 = np.random.uniform(cont_bounds[3][0], cont_bounds[3][1])
        gm_ID_5 = np.random.uniform(cont_bounds[4][0], cont_bounds[4][1])
        gm_ID_6 = np.random.uniform(cont_bounds[5][0], cont_bounds[5][1])
        
        L_1_idx = np.random.randint(0, n_L_values)
        L_2_idx = np.random.randint(0, n_L_values)
        L_3_idx = np.random.randint(0, n_L_values)
        L_4_idx = np.random.randint(0, n_L_values)
        L_5_idx = np.random.randint(0, n_L_values)
        L_6_idx = np.random.randint(0, n_L_values)

        I_T = np.random.uniform(cont_bounds[6][0], cont_bounds[6][1])
        
        particle = np.array([gm_ID_1, gm_ID_2, gm_ID_3, gm_ID_4, gm_ID_5, gm_ID_6, 
                             L_1_idx, L_2_idx, L_3_idx, L_4_idx, L_5_idx, L_6_idx, I_T])
        
        passed, area, specs = survivability_test(particle)

        if passed:
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
            
        else:
            sim_passed = False
        
        if sim_passed:
            print(f"\ngm_ID_1: {gm_ID_1:.2f}, gm_ID_2: {gm_ID_2:.2f}, gm_ID_3: {gm_ID_3:.2f}, gm_ID_4: {gm_ID_4:.2f}, gm_ID_5: {gm_ID_5:.2f}, gm_ID_6: {gm_ID_6:.2f}, I_T: {I_T*1e6:.2f} μA")
            print(f"L_1: {meas['L_1']:.2f} μm, L_2: {meas['L_2']:.2f} μm, L_3: {meas['L_3']:.2f} μm, L_4: {meas['L_4']:.2f} μm, L_5: {meas['L_5']:.2f} μm, L_6: {meas['L_6']:.2f} μm")
            print(f"Gain: {meas['Gain_dB']:.2f} dB, GBW: {meas['GBW']*1e-6:.2f} MHz, PM: {meas['PM']:.2f} degrees, SR: {meas['SR']*1e-6:.2f} V/μs, CMRR: {meas['CMRR_dB']:.2f} dB, PSRR: {meas['PSRR_dB']:.2f} dB, Power: {meas['Power']*1e6:.2f} μW")
            return particle, area, meas
            
    return None, np.inf, None

def generate_N_particles(cont_bounds, n_L_values, N, verbose=False):

    particles = []
    areas = []
    specs_list = []
    
    if verbose:
        print(f"Generating {N} valid particles...")
    
    for i in range(N):
        particle, area, specs = generate_initial_particle(cont_bounds, n_L_values)
        
        if particle is not None:
            particles.append(particle)
            areas.append(area)
            specs_list.append(specs)
            if verbose:
                print(f"  Particle {i+1}/{N}: Area = {area:.2f} μm²")
        else:
            if verbose:
                print(f"  Particle {i+1}/{N}: Failed to generate valid particle")
            return None, None, None
    
    return np.array(particles), np.array(areas), specs_list

def refill_rejected_particles(particles, fitness, cont_bounds, n_L_values, rejected_mask):

    n_rejected = np.sum(rejected_mask)
    
    if n_rejected == 0:
        return particles, fitness
    
    print(f"  Refilling {n_rejected} rejected particles...")
    
    for idx in np.where(rejected_mask)[0]:
        particle, area, specs = generate_particle(cont_bounds, n_L_values)
        
        if particle is not None:
            particles[idx] = particle
            fitness[idx] = area
            print(f"    Particle {idx}: Refilled with Area = {area:.2f} μm²")
        else:
            print(f"    Particle {idx}: Failed to refill")
    
    return particles, fitness