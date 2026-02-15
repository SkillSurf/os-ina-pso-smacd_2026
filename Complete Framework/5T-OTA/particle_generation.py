import numpy as np
from survivability_check import survivability_test, L_DISCRETE_VALUES

def generate_particle(cont_bounds, n_L_values, max_attempts=1000):

    for attempt in range(max_attempts):
        gm1 = np.random.uniform(cont_bounds[0][0], cont_bounds[0][1])
        gm2 = np.random.uniform(cont_bounds[1][0], cont_bounds[1][1])
        ID = np.random.uniform(cont_bounds[2][0], cont_bounds[2][1])
        
        L_1_idx = np.random.randint(0, n_L_values)
        L_2_idx = np.random.randint(0, n_L_values)
        
        particle = np.array([gm1, gm2, L_1_idx, L_2_idx, ID])
        
        passed, area, specs = survivability_test(particle)
        
        if passed:
            return particle, area, specs
    
    return None, np.inf, None

def generate_N_particles(cont_bounds, n_L_values, N, verbose=False):

    particles = []
    areas = []
    specs_list = []
    
    if verbose:
        print(f"Generating {N} valid particles...")
    
    for i in range(N):
        particle, area, specs = generate_particle(cont_bounds, n_L_values)
        
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