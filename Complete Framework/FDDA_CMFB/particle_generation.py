import numpy as np
from gmID_sizing import get_W
from simulator import evaluate_design
from survivability_check import survivability_test
from specs import L_DISCRETE_VALUES

def generate_particle(cont_bounds, n_L_values, max_attempts=1000):

    for attempt in range(max_attempts):
        gm_ID_1 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_2 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_3 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_4 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_5 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_6 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])

        I_T = np.random.uniform(cont_bounds[1][0], cont_bounds[1][1])
        I_X = np.random.uniform(cont_bounds[2][0], cont_bounds[2][1])
        
        V_A = np.random.uniform(cont_bounds[3][0], cont_bounds[3][1])
        V_B = np.random.uniform(cont_bounds[4][0], cont_bounds[4][1])
        V_C = np.random.uniform((V_B + 0.1), cont_bounds[5][1])
        
        L_1_idx = np.random.randint(0, n_L_values)
        L_2_idx = np.random.randint(0, n_L_values)
        L_3_idx = np.random.randint(0, n_L_values)
        L_4_idx = np.random.randint(0, n_L_values)
        L_5_idx = np.random.randint(0, n_L_values)
        L_6_idx = np.random.randint(0, n_L_values)
        L_7_idx = np.random.randint(0, n_L_values)
        L_8_idx = np.random.randint(0, n_L_values)
        
    #     particle = np.array([gm1, gm2, L_1_idx, L_2_idx, ID])
        
    #     passed, area, specs = survivability_test(particle)
        
    #     if passed:
    #         return particle, area, specs
    
    return None, np.inf, None

def generate_initial_particle(cont_bounds, n_L_values, max_attempts=1000):

    for attempt in range(max_attempts):
        gm_ID_1 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_2 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_3 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_4 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_5 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm_ID_6 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])

        I_T = np.random.uniform(cont_bounds[1][0], cont_bounds[1][1])
        I_X = np.random.uniform(cont_bounds[2][0], cont_bounds[2][1])
        
        V_A = np.random.uniform(cont_bounds[3][0], cont_bounds[3][1])
        V_B = np.random.uniform(cont_bounds[4][0], cont_bounds[4][1])
        V_C = np.random.uniform((V_B + 0.1), cont_bounds[5][1])
        
        L_1_idx = np.random.randint(0, n_L_values)
        L_2_idx = np.random.randint(0, n_L_values)
        L_3_idx = np.random.randint(0, n_L_values)
        L_4_idx = np.random.randint(0, n_L_values)
        L_5_idx = np.random.randint(0, n_L_values)
        L_6_idx = np.random.randint(0, n_L_values)
        L_7_idx = np.random.randint(0, n_L_values)
        L_8_idx = np.random.randint(0, n_L_values)
        
    #     particle = np.array([gm1, gm2, L_1_idx, L_2_idx, ID])
    #     passed, area, specs = survivability_test(particle)

    #     L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
    #     L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
    #     W_1, W_2, _, _, _ = get_W(gm1, gm2, L_1, L_2, ID)

    #     if passed and W_1 is not None and W_2 is not None:
    #         sim_passed, meas = evaluate_design(W_1, L_1, W_2, L_2, ID*1e6)
    #     else:
    #         sim_passed = False
        
    #     if sim_passed:
    #         specs['SR'] = meas['SR_meas']
    #         specs['GBW'] = meas['GBW_meas']
    #         specs['Gain_dB'] = meas['Gain_meas_dB']
    #         specs['Gain'] = 10**(meas['Gain_meas_dB']/20)
    #         specs['PM'] = meas['PM_meas']
    #         specs['Power'] = meas['Power_meas']
    #         return particle, area, specs
    
    return None, np.inf, None

def generate_N_particles(cont_bounds, n_L_values, N, verbose=False):

    # particles = []
    # areas = []
    # specs_list = []
    
    # if verbose:
    #     print(f"Generating {N} valid particles...")
    
    # for i in range(N):
    #     particle, area, specs = generate_initial_particle(cont_bounds, n_L_values)
        
    #     if particle is not None:
    #         particles.append(particle)
    #         areas.append(area)
    #         specs_list.append(specs)
    #         if verbose:
    #             print(f"  Particle {i+1}/{N}: Area = {area:.2f} μm²")
    #     else:
    #         if verbose:
    #             print(f"  Particle {i+1}/{N}: Failed to generate valid particle")
    #         return None, None, None
    
    return np.array(particles), np.array(areas), specs_list

def refill_rejected_particles(particles, fitness, cont_bounds, n_L_values, rejected_mask):

    # n_rejected = np.sum(rejected_mask)
    
    # if n_rejected == 0:
    #     return particles, fitness
    
    # print(f"  Refilling {n_rejected} rejected particles...")
    
    # for idx in np.where(rejected_mask)[0]:
    #     particle, area, specs = generate_particle(cont_bounds, n_L_values)
        
    #     if particle is not None:
    #         particles[idx] = particle
    #         fitness[idx] = area
    #         print(f"    Particle {idx}: Refilled with Area = {area:.2f} μm²")
    #     else:
    #         print(f"    Particle {idx}: Failed to refill")
    
    return particles, fitness