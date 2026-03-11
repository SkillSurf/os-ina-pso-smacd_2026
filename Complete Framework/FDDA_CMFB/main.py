import os
import gc
import time
import psutil
import logging
import numpy as np
import matplotlib.pyplot as plt

from specs import *
from gmID_sizing import get_params, get_feasRegion
from survivability_check import survivability_test
from particle_generation import generate_N_particles, generate_particle
from pso import PSO
from simulator import evaluate_design

process = psutil.Process(os.getpid())
logger = logging.getLogger("OptimizationLogger")
logger.setLevel(logging.INFO)

logger.propagate = False  # Prevent duplicate logs if root logger is configured
if logger.hasHandlers():
    logger.handlers.clear()

def main():

    file_handler = logging.FileHandler("optimization_log.txt", mode='w', encoding="utf-8")

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    # Log the current time at the start of the particle generation
    logger.info(f"PARTICLE GENERATION STARTED\n")
       
    L_available, n_L_values, I_T_min, I_T_max = get_feasRegion(L_DISCRETE_VALUES)
    
    cont_bounds = [
        (gm_ID_1_range[0], gm_ID_1_range[1]),
        (gm_ID_2_range[0], gm_ID_2_range[1]),
        (gm_ID_3_range[0], gm_ID_3_range[1]),
        (gm_ID_4_range[0], gm_ID_4_range[1]),
        (gm_ID_5_range[0], gm_ID_5_range[1]),
        (gm_ID_6_range[0], gm_ID_6_range[1]),
        (I_T_min, I_T_max)
    ]

    # Cache original gm_ID bounds as absolute outer limits (never changes)
    original_gm_bounds = [
        (gm_ID_1_range[0], gm_ID_1_range[1]),
        (gm_ID_2_range[0], gm_ID_2_range[1]),
        (gm_ID_3_range[0], gm_ID_3_range[1]),
        (gm_ID_4_range[0], gm_ID_4_range[1]),
        (gm_ID_5_range[0], gm_ID_5_range[1]),
        (gm_ID_6_range[0], gm_ID_6_range[1]),
    ]
    
    print(f"Feasible Region Done")

    start_time = time.time()
    
    particles, fitness, specs_list = generate_N_particles(
        cont_bounds, n_L_values, N_PARTICLES, verbose=True
    )
    
    if particles is None:
        print("\nERROR: Failed to generate initial particles!")
        return None
    
    end_time = time.time()
    particle_gen_time = end_time - start_time
    print(f"\nTime taken to generate particles: {particle_gen_time:.2f} seconds")

    # Log all initial particles and their fitness values
    for i in range(len(particles)):
        log_init_particle(i, particles[i], fitness[i])

    # Log current time at the end of particle generation
    logger.info(f"PARTICLE GENERATION COMPLETED\n")

    # Log time taken to generate particles
    logger.info(f"Time taken to generate {N_PARTICLES} particles: {particle_gen_time:.2f} seconds | {(particle_gen_time) / 3600:.2f} hours\n")
    
    print(f"\nSuccessfully generated {N_PARTICLES} valid particles")
    print(f"Initial best area: {np.min(fitness):.2f} μm²")
    
    print("\nInitializing PSO optimizer...")
    print("-"*70)

    # Log the current time at the start of the optimization
    logger.info(f"OPTIMIZATION STARTED\n")
    
    pso = PSO(
        cont_bounds=cont_bounds,
        n_L_values=n_L_values,
        n_particles=N_PARTICLES,
        w=0.7,
        c1=1.7,
        c2=1.7,
        max_velocity_updates=MAX_VELOCITY_UPDATES
    )
    
    pso.initialize_velocities()
    pso.set_initial_best(particles, fitness, specs_list)
    
    print(f"PSO initialized with {N_PARTICLES} particles")
    print(f"Global best: {pso.gbest_fitness:.2f} μm²")
    # Log initial best solution
    log_solution(0, pso.gbest_position, pso.gbest_specs, pso.gbest_fitness)
    
    gbest_history = [pso.gbest_fitness]
    avg_fitness_history = [np.mean(fitness)]
    
    start_time = time.time()
    
    for iteration in range(MAX_ITERATIONS):

        gc.collect()  # Explicitly trigger garbage collection to manage memory
        particles, fitness, need_simulator_check = pso.update_swarm(particles, fitness)
        
        print(f"\nIteration {iteration+1}: Updated {len(need_simulator_check)} particles")
        print(f"  Current global best: {pso.gbest_fitness:.2f} μm²")

        if len(need_simulator_check) > 0:

            rejected_indices = []
            
            for idx in need_simulator_check:
                particle = particles[idx]
                
                gm_ID_1, gm_ID_2, gm_ID_3, gm_ID_4, gm_ID_5, gm_ID_6 = particle[0:6]
                L_1_idx, L_2_idx, L_3_idx, L_4_idx, L_5_idx, L_6_idx, L_7_idx = particle[6:13]
                I_T = particle[13]
                
                L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
                L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
                L_3 = L_DISCRETE_VALUES[int(L_3_idx)]
                L_4 = L_DISCRETE_VALUES[int(L_4_idx)]
                L_5 = L_DISCRETE_VALUES[int(L_5_idx)]
                L_6 = L_DISCRETE_VALUES[int(L_6_idx)]
                L_7 = L_DISCRETE_VALUES[int(L_7_idx)]

                gm_ID = {'gm_ID_1': gm_ID_1, 'gm_ID_2': gm_ID_2, 'gm_ID_3': gm_ID_3, 
                         'gm_ID_4': gm_ID_4, 'gm_ID_5': gm_ID_5, 'gm_ID_6': gm_ID_6}

                L = {'L_1': L_1, 'L_2': L_2, 'L_3': L_3, 'L_4': L_4, 'L_5': L_5, 'L_6': L_6, 'L_7': L_7}

                # Get W, L, and Vgs values
                W, L, _, _, Vgs, _, _ = get_params(gm_ID, L, V_A, V_B, I_T)
                
                if W is not None and not any(w is None for w in W.values()):
                    print(f"  Particle {idx+1}: Simulating...")
                    
                    current_params = {
                        'W_1': W['W_1'], 'L_1': L['L_1'],
                        'W_2': W['W_2'], 'L_2': L['L_2'],
                        'W_3': W['W_3'], 'L_3': L['L_3'],
                        'W_4': W['W_4'], 'L_4': L['L_4'],
                        'W_5': W['W_5'], 'L_5': L['L_5'],
                        'W_6': W['W_6'], 'L_6': L['L_6'],
                        'W_7': W['W_7'], 'L_7': L['L_7'],
                        'W_8': W['W_8'], 'L_8': L['L_8'],
                        'V_B1': VDD - Vgs['Vgs_6'],
                        'V_B2': Vgs['Vgs_5'],
                        'V_B3': V_B + Vgs['Vgs_4'],
                        'V_B4': V_A - Vgs['Vgs_3'],
                        'V_CM': VCM
                    }
                    # Run simulator
                    sim_passed, _ = evaluate_design(current_params)
                    
                    if not sim_passed:
                        print(f"    Particle {idx+1}: REJECTED by simulator")
                        rejected_indices.append(idx)
                        fitness[idx] = np.inf  # Mark as infeasible
                    else:
                        print(f"    Particle {idx+1}: PASSED simulator")
                else:
                    print(f"  Particle {idx+1}: Invalid W/L values, skipping simulation")
                    rejected_indices.append(idx)
                    fitness[idx] = np.inf
            
            # Velocity updates for rejected particles from the simulator
            if len(rejected_indices) > 0:
                print(f"\nPerforming velocity updates for {len(rejected_indices)} rejected particles...")

                for idx in rejected_indices:
                    # Try multiple velocity updates to recover the particle
                    for attempt in range(MAX_VELOCITY_UPDATES):
                        offspring, area, specs, success = pso.generate_offspring(idx, particles[idx])
                        
                        if success and area < np.inf:
                            # Check with simulator again
                            gm_ID_1, gm_ID_2, gm_ID_3, gm_ID_4, gm_ID_5, gm_ID_6 = offspring[0:6]
                            L_1_idx, L_2_idx, L_3_idx, L_4_idx, L_5_idx, L_6_idx, L_7_idx = offspring[6:13]
                            I_T = offspring[13]
                            
                            L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
                            L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
                            L_3 = L_DISCRETE_VALUES[int(L_3_idx)]
                            L_4 = L_DISCRETE_VALUES[int(L_4_idx)]
                            L_5 = L_DISCRETE_VALUES[int(L_5_idx)]
                            L_6 = L_DISCRETE_VALUES[int(L_6_idx)]
                            L_7 = L_DISCRETE_VALUES[int(L_7_idx)]
                            
                            gm_ID = {'gm_ID_1': gm_ID_1, 'gm_ID_2': gm_ID_2, 'gm_ID_3': gm_ID_3, 
                                     'gm_ID_4': gm_ID_4, 'gm_ID_5': gm_ID_5, 'gm_ID_6': gm_ID_6}
                            
                            L = {'L_1': L_1, 'L_2': L_2, 'L_3': L_3, 'L_4': L_4, 'L_5': L_5, 'L_6': L_6, 'L_7': L_7}                

                            # Get W, L, and Vgs values
                            W, L, _, _, Vgs, _, _ = get_params(gm_ID, L, V_A, V_B, I_T)
                
                            if W is not None and not any(w is None for w in W.values()):
                                current_params = {
                                    'W_1': W['W_1'], 'L_1': L['L_1'],
                                    'W_2': W['W_2'], 'L_2': L['L_2'],
                                    'W_3': W['W_3'], 'L_3': L['L_3'],
                                    'W_4': W['W_4'], 'L_4': L['L_4'],
                                    'W_5': W['W_5'], 'L_5': L['L_5'],
                                    'W_6': W['W_6'], 'L_6': L['L_6'],
                                    'W_7': W['W_7'], 'L_7': L['L_7'],
                                    'W_8': W['W_8'], 'L_8': L['L_8'],
                                    'V_B1': VDD - Vgs['Vgs_6'],
                                    'V_B2': Vgs['Vgs_5'],
                                    'V_B3': V_B + Vgs['Vgs_4'],
                                    'V_B4': V_A - Vgs['Vgs_3'],
                                    'V_CM': VCM
                                }

                                sim_passed, _ = evaluate_design(current_params)
                                
                                if sim_passed:
                                    particles[idx] = offspring
                                    fitness[idx] = area
                                    print(f"    Particle {idx+1}: Recovered with velocity update (Area={area:.2f})")
                                    break
                    
                    # If still rejected after velocity updates, mark for regeneration
                    if fitness[idx] == np.inf:
                        print(f"    Particle {idx+1}: Failed all velocity updates")
            
            print("\nUpdating personal and global bests...")
            for i in range(N_PARTICLES):
                if fitness[i] < np.inf and fitness[i] < pso.pbest_fitness[i]:
                    pso.pbest_fitness[i] = fitness[i]
                    pso.pbest_positions[i] = particles[i].copy()
                    print(f"  Particle {i+1}: Updated pbest = {fitness[i]:.2f} μm²")
            
            best_idx = np.argmin(fitness)
            if fitness[best_idx] < np.inf and fitness[best_idx] < pso.gbest_fitness:
                pso.gbest_fitness = fitness[best_idx]
                pso.gbest_position = particles[best_idx].copy()
                _, _, specs_dict = survivability_test(particles[best_idx])
                pso.gbest_specs = specs_dict
                print(f"  New global best: {fitness[best_idx]:.2f} μm²")
                # Log new best solution
                log_solution(iteration, pso.gbest_position, pso.gbest_specs, pso.gbest_fitness)
            
                # Dynamically adjust gm_ID search bounds based on the best solution
                DELTA = 1.0  
                best_gm_IDs = pso.gbest_position[0:6]

                for i, gm_val in enumerate(best_gm_IDs):
                    orig_lo, orig_hi = original_gm_bounds[i]  # currently this is not needed
                    new_lo = gm_val - DELTA
                    new_hi = gm_val + DELTA

                    cont_bounds[i] = (new_lo, new_hi)

                print(f"  [Bounds Update] New gm_ID search window:")
                for i, (lo, hi) in enumerate(cont_bounds[:6]):
                    print(f"    gm_ID_{i+1}_range = ({lo:.4f}, {hi:.4f})")

            # Refill rejected particles with new random particles
            rejected_mask = fitness == np.inf
            n_rejected = np.sum(rejected_mask)
            
            if n_rejected > 0:

                refill_count = 0
                for idx in np.where(rejected_mask)[0]:
                    # New particle generation for rejected particles
                    new_particle, new_area, new_specs = generate_particle(cont_bounds, n_L_values)
                    
                    if new_particle is not None:
                        # Check survivability (already done in generate_particle)
                        particles[idx] = new_particle
                        fitness[idx] = new_area
                        refill_count += 1
                        print(f"    Particle {idx+1}: Refilled (Area={new_area:.2f})")
                    else:
                        print(f"    Particle {idx+1}: Failed to refill")
                
                print(f"  Successfully refilled {refill_count}/{n_rejected} particles")
        
        gbest_history.append(pso.gbest_fitness)
        avg_fitness_history.append(np.mean(fitness[fitness < np.inf]))
        
        valid_fitness = fitness[fitness < np.inf]
        print(f"\nIteration {iteration+1} Summary:")
        print(f"  Global Best: {pso.gbest_fitness:.2f} μm²")

        if len(valid_fitness) > 0:
            print(f"  Average:     {np.mean(valid_fitness):.2f} μm²")
        print(f"  Valid particles: {len(valid_fitness)}/{N_PARTICLES}")
        print(f"  --- Memory Usage: {process.memory_info().rss / (1024 ** 2):.2f} MB ({process.memory_info().rss / (1024 ** 3):.2f} GB)")
    
    end_time = time.time()
    optimization_time = end_time - start_time

    print("\nOptimization is complete!")

    # Log the total number of iterations
    logger.info(f"Total number of iterations in this run: {MAX_ITERATIONS}\n")
    
    # Log optimization time
    logger.info(f"Total optimization time: {optimization_time:.2f} seconds | {(optimization_time) / 3600:.2f} hours\n")

    print("\nExtracting final design parameters...")
    
    best_solution = pso.get_best_solution()
    
    gm_ID_1 = best_solution['gm_ID_1']
    gm_ID_2 = best_solution['gm_ID_2']
    gm_ID_3 = best_solution['gm_ID_3']
    gm_ID_4 = best_solution['gm_ID_4']
    gm_ID_5 = best_solution['gm_ID_5']
    gm_ID_6 = best_solution['gm_ID_6']
    L_1 = best_solution['L_1']
    L_2 = best_solution['L_2']
    L_3 = best_solution['L_3']
    L_4 = best_solution['L_4']
    L_5 = best_solution['L_5']
    L_6 = best_solution['L_6']
    L_7 = best_solution['L_7']
    I_T = best_solution['I_T']
    
    gm_ID = {'gm_ID_1': gm_ID_1, 'gm_ID_2': gm_ID_2, 'gm_ID_3': gm_ID_3, 
             'gm_ID_4': gm_ID_4, 'gm_ID_5': gm_ID_5, 'gm_ID_6': gm_ID_6}
    
    L = {'L_1': L_1, 'L_2': L_2, 'L_3': L_3, 'L_4': L_4, 'L_5': L_5, 'L_6': L_6, 'L_7': L_7}
    
    W, L, _, _, Vgs, _, _ = get_params(gm_ID, L, V_A, V_B, I_T)
                
    current_params = {
        'W_1': W['W_1'], 'L_1': L['L_1'],
        'W_2': W['W_2'], 'L_2': L['L_2'],
        'W_3': W['W_3'], 'L_3': L['L_3'],
        'W_4': W['W_4'], 'L_4': L['L_4'],
        'W_5': W['W_5'], 'L_5': L['L_5'],
        'W_6': W['W_6'], 'L_6': L['L_6'],
        'W_7': W['W_7'], 'L_7': L['L_7'],
        'W_8': W['W_8'], 'L_8': L['L_8'],
        'V_B1': VDD - Vgs['Vgs_6'],
        'V_B2': Vgs['Vgs_5'],
        'V_B3': V_B + Vgs['Vgs_4'],
        'V_B4': V_A - Vgs['Vgs_3'],
        'V_CM': VCM
    }
    
    print("\nOptimal Design Parameters:")
    print(f"  gm/ID_1 = {gm_ID_1:.2f} S/A")
    print(f"  gm/ID_2 = {gm_ID_2:.2f} S/A")
    print(f"  gm/ID_3 = {gm_ID_3:.2f} S/A")
    print(f"  gm/ID_4 = {gm_ID_4:.2f} S/A")
    print(f"  gm/ID_5 = {gm_ID_5:.2f} S/A")
    print(f"  gm/ID_6 = {gm_ID_6:.2f} S/A")
    print(f"  I_T     = {I_T*1e6:.2f} μA")
    print(f"  V_A     = {V_A:.2f} V")
    print(f"  V_B     = {V_B:.2f} V")
    
    print("\nOptimal Transistor Sizing:")
    print(f"  W_1 = {W['W_1']:.2f} μm,  L_1 = {L['L_1']:.2f} μm")
    print(f"  W_2 = {W['W_2']:.2f} μm,  L_2 = {L['L_2']:.2f} μm")
    print(f"  W_3 = {W['W_3']:.2f} μm,  L_3 = {L['L_3']:.2f} μm")
    print(f"  W_4 = {W['W_4']:.2f} μm,  L_4 = {L['L_4']:.2f} μm")
    print(f"  W_5 = {W['W_5']:.2f} μm,  L_5 = {L['L_5']:.2f} μm")
    print(f"  W_6 = {W['W_6']:.2f} μm,  L_6 = {L['L_6']:.2f} μm")
    print(f"  W_7 = {W['W_7']:.2f} μm,  L_7 = {L['L_7']:.2f} μm")
    print(f"  W_8 = {W['W_8']:.2f} μm,  L_8 = {L['L_8']:.2f} μm")
    print(f"  V_B1 = {current_params['V_B1']:.4f} V")
    print(f"  V_B2 = {current_params['V_B2']:.4f} V")
    print(f"  V_B3 = {current_params['V_B3']:.4f} V")
    print(f"  V_B4 = {current_params['V_B4']:.4f} V")
    
    print(f"\n OPTIMAL AREA: {best_solution['area']:.4f} μm²")

    print("\nFinal Simulator Verification...")
    
    final_check, final_results = evaluate_design(current_params, plots=True)
    print(f"Final design {'PASSED' if final_check else 'FAILED'} simulator check")
    
    if final_results is not None:
        print("\nPerformance Specifications:")
        print(f"  Gain:         {final_results['Gain_dB']:.2f} dB      (spec: ≥{Gain_dc_spec_dB:.2f})")
        print(f"  GBW:          {final_results['GBW']*1e-6:.2f} MHz      (spec: ≥{GBW_spec*1e-6:.2f})")
        print(f"  Phase Margin: {final_results['PM']:.2f}°        (spec: ≥{PM_spec:.2f})")
        print(f"  Slew Rate:    {final_results['SR']*1e-6:.2f} V/μs     (spec: ≥{SR_spec*1e-6:.2f})")
        print(f"  Power:        {final_results['Power']*1e6:.2f} μW       (spec: ≤{Power_spec*1e6:.2f})")
        print(f"  CMRR @ 1kHz:  {final_results['CMRR_dB']:.2f} dB      (spec: ≥{CMRR_spec_dB:.2f})")
        print(f"  PSRR @ 1kHz:  {final_results['PSRR_dB']:.2f} dB      (spec: ≥{PSRR_spec_dB:.2f})")
    
    print(f"\nOptimization Time: {optimization_time:.2f} seconds")
    print("="*70)
    
    plot_convergence(gbest_history, avg_fitness_history)
    
    save_results(best_solution, W, L, optimization_time, final_check, final_results)
    
    # Log current time at the end of the optimization
    logger.info(f"OPTIMIZATION COMPLETED\n")

    # Log total run time
    logger.info(f"Total run time: {(particle_gen_time + optimization_time):.2f} seconds | {(particle_gen_time + optimization_time) / 3600:.2f} hours\n")

    return best_solution

def log_init_particle(particle, position, fitness):

    # Log best position data into a .txt file
    raw_particle = [float(val) for val in position]

    # Create a formatted log message
    log_message = (
        f"Initial Particle {particle + 1} | Active Area: {fitness:.4f} μm²\n"
    )
    log_message += f"gm/ID_1 = {raw_particle[0]:.4f} S/A, gm/ID_2 = {raw_particle[1]:.4f} S/A, gm/ID_3 = {raw_particle[2]:.4f} S/A\n"
    log_message += f"gm/ID_4 = {raw_particle[3]:.4f} S/A, gm/ID_5 = {raw_particle[4]:.4f} S/A, gm/ID_6 = {raw_particle[5]:.4f} S/A, I_T = {raw_particle[13]*1e6:.4f} μA\n"
    log_message += f"L_1 = {L_DISCRETE_VALUES[int(raw_particle[6])]:.2f} μm, L_2 = {L_DISCRETE_VALUES[int(raw_particle[7])]:.2f} μm, L_3 = {L_DISCRETE_VALUES[int(raw_particle[8])]:.2f} μm, L_4 = {L_DISCRETE_VALUES[int(raw_particle[9])]:.2f} μm, L_5 = {L_DISCRETE_VALUES[int(raw_particle[10])]:.2f} μm, L_6 = {L_DISCRETE_VALUES[int(raw_particle[11])]:.2f} μm, L_7 = {L_DISCRETE_VALUES[int(raw_particle[12])]:.2f} μm\n"   

    # Write the log message to the file
    logger.info(log_message)  

def log_solution(iteration, position, specs, fitness):

    # Log best position data into a .txt file
    raw_particle = [float(val) for val in position]
    raw_particle[-1] *= 1e6  # Scale the last element (I_T) to μA
    clean_particle = [
        f"{L_DISCRETE_VALUES[int(val)]}" if 6 <= i <= 12 
        else f"{val:.4f}" 
        for i, val in enumerate(raw_particle)
    ]
    
    clean_specs = {k: float(v) for k, v in specs.items()}

    # Create a formatted log message
    log_message = (
        f"Iteration {iteration + 1} | Global Best Area: {fitness:.4f} μm²\n"
        f"    Particle : [{', '.join(clean_particle)}]\n"
        f"    Specs    :\n"
    )

    keys_to_skip = {'Gain_dB', 'GBW', 'PM', 'SR', 'Power', 'V_CMFB', 'CMRR_dB', 'PSRR_dB', 'Area'}

    for key, value in clean_specs.items():
        if key in keys_to_skip:
            continue            
        elif key.startswith('W_') or key.startswith('L_'):
            log_message += f"        {key:<8}: {value:.2f} μm\n"            
        elif key.startswith('V_'):
            log_message += f"        {key:<8}: {value:.4f} V\n"
        else:
            log_message += f"        {key:<8}: {value:.4g}\n"

    # Write the log message to the file
    logger.info(log_message)  

def plot_convergence(gbest_history, avg_history):

    # Log convergence data
    for i, area in enumerate(gbest_history):
        logger.info(f"Iteration {i+1}: Global Best Area = {area:.4f} μm², Average Area = {avg_history[i]:.4f} μm²\n")

    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(gbest_history, 'b-', linewidth=2, marker='o', markersize=4)
    plt.xlabel('Iteration', fontsize=11)
    plt.ylabel('Global Best Area (μm²)', fontsize=11)
    plt.title('Convergence - Global Best', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(avg_history, 'g-', linewidth=2, marker='s', markersize=4, label='Average')
    plt.plot(gbest_history, 'r--', linewidth=2, marker='o', markersize=4, label='Global Best')
    plt.xlabel('Iteration', fontsize=11)
    plt.ylabel('Area (μm²)', fontsize=11)
    plt.title('Swarm Statistics', fontsize=12, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('optimization_convergence.png', dpi=300, bbox_inches='tight')
    print("\nConvergence plot saved to 'optimization_convergence.png'")

def save_results(best_solution, W, L, opt_time, sim_passed, results):
    with open('optimization_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("FDDA-CMFB OPTIMIZATION RESULTS\n")
        f.write("="*70 + "\n\n")
        
        f.write("DESIGN SPECIFICATIONS:\n")
        f.write(f"  VDD = {VDD} V\n")
        f.write(f"  CL = {CL*1e12:.2f} pF\n")
        f.write(f"  Gain ≥ {Gain_dc_spec_dB:.2f} dB\n")
        f.write(f"  GBW ≥ {GBW_spec*1e-6:.2f} MHz\n")
        f.write(f"  Phase Margin ≥ {PM_spec:.2f}°\n")
        f.write(f"  Slew Rate ≥ {SR_spec*1e-6:.2f} V/μs\n")
        f.write(f"  Power ≤ {Power_spec*1e6:.2f} μW\n")
        f.write(f"  CMRR @ 1kHz ≥ {CMRR_spec_dB:.2f} dB\n")
        f.write(f"  PSRR @ 1kHz ≥ {PSRR_spec_dB:.2f} dB\n\n")
        
        f.write("OPTIMAL DESIGN PARAMETERS:\n")
        f.write(f"  gm/ID_1 = {best_solution['gm_ID_1']:.2f} S/A\n")
        f.write(f"  gm/ID_2 = {best_solution['gm_ID_2']:.2f} S/A\n")
        f.write(f"  gm/ID_3 = {best_solution['gm_ID_3']:.2f} S/A\n")
        f.write(f"  gm/ID_4 = {best_solution['gm_ID_4']:.2f} S/A\n")
        f.write(f"  gm/ID_5 = {best_solution['gm_ID_5']:.2f} S/A\n")
        f.write(f"  gm/ID_6 = {best_solution['gm_ID_6']:.2f} S/A\n")
        f.write(f"  I_T     = {best_solution['I_T']*1e6:.2f} μA\n")
        f.write(f"  V_A     = {V_A:.2f} V\n")
        f.write(f"  V_B     = {V_B:.2f} V\n\n")
        
        f.write("OPTIMAL TRANSISTOR SIZING:\n")
        f.write(f"  W_1 = {results['W_1']:.2f} μm,  L_1 = {results['L_1']:.2f} μm\n")
        f.write(f"  W_2 = {results['W_2']:.2f} μm,  L_2 = {results['L_2']:.2f} μm\n")
        f.write(f"  W_3 = {results['W_3']:.2f} μm,  L_3 = {results['L_3']:.2f} μm\n")
        f.write(f"  W_4 = {results['W_4']:.2f} μm,  L_4 = {results['L_4']:.2f} μm\n")
        f.write(f"  W_5 = {results['W_5']:.2f} μm,  L_5 = {results['L_5']:.2f} μm\n")
        f.write(f"  W_6 = {results['W_6']:.2f} μm,  L_6 = {results['L_6']:.2f} μm\n")
        f.write(f"  W_7 = {results['W_7']:.2f} μm,  L_7 = {results['L_7']:.2f} μm\n")
        f.write(f"  W_8 = {results['W_8']:.2f} μm,  L_8 = {results['L_8']:.2f} μm\n")
        f.write(f"  V_B1 = {results['V_B1']:.4f} V\n")
        f.write(f"  V_B2 = {results['V_B2']:.4f} V\n")
        f.write(f"  V_B3 = {results['V_B3']:.4f} V\n")
        f.write(f"  V_B4 = {results['V_B4']:.4f} V\n\n")
        
        f.write(f"OPTIMAL AREA: {best_solution['area']:.2f} μm²\n\n")
        
        if results is not None:
            f.write("ACHIEVED SPECIFICATIONS:\n")
            f.write(f"  Gain         = {results['Gain_dB']:.2f} dB\n")
            f.write(f"  GBW          = {results['GBW']*1e-6:.2f} MHz\n")
            f.write(f"  Phase Margin = {results['PM']:.2f}°\n")
            f.write(f"  Slew Rate    = {results['SR']*1e-6:.2f} V/μs\n")
            f.write(f"  Power        = {results['Power']*1e6:.2f} μW\n")
            f.write(f"  CMRR @ 1kHz  = {results['CMRR_dB']:.2f} dB\n")
            f.write(f"  PSRR @ 1kHz  = {results['PSRR_dB']:.2f} dB\n\n")
        
        f.write(f"OPTIMIZATION TIME: {opt_time:.2f} seconds\n")
        f.write(f"FINAL SIMULATOR CHECK: {'PASSED' if sim_passed else 'FAILED'}\n")
    
    print("Results saved to 'optimization_results.txt'")

if __name__ == "__main__":
    results = main()