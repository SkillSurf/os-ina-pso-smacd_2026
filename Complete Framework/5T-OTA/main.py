import time
import numpy as np
import matplotlib.pyplot as plt

from specs import *
from gmID_sizing import get_W, get_feasRegion
from survivability_check import survivability_test
from particle_generation import generate_N_particles, generate_particle
from pso import PSO
from simulator import evaluate_design

def main():
    
    gm1_min, gm1_max, gm2_min, gm2_max, L_available, n_L_values, ID_min, ID_max = \
        get_feasRegion(gm_ID_range, L_DISCRETE_VALUES, SR_spec, CL, Power_spec, GBW_spec)
    
    cont_bounds = [
        (gm1_min, gm1_max),
        (gm2_min, gm2_max),
        (ID_min, ID_max)
    ]
    
    print(f"Feasible Region Done")
    
    particles, fitness, specs_list = generate_N_particles(
        cont_bounds, n_L_values, N_PARTICLES, verbose=True
    )
    
    if particles is None:
        print("\nERROR: Failed to generate initial particles!")
        return None
    
    print(f"\nSuccessfully generated {N_PARTICLES} valid particles")
    
    print("\nInitializing PSO optimizer...")
    
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
    
    # Tracking variables
    gbest_history = [pso.gbest_fitness]
    avg_fitness_history = [np.mean(fitness)]
    
    start_time = time.time()
    
    # Main Loop
    for iteration in range(MAX_ITERATIONS):
        
        print("\nRunning PSO update...")
        particles, fitness, need_simulator_check = pso.update_swarm(particles, fitness)
        
        print(f"  Updated {len(need_simulator_check)} particles")

        if len(need_simulator_check) > 0:
            print(f"\nChecking {len(need_simulator_check)} particles with simulator...")
            
            rejected_indices = []
            
            for idx in need_simulator_check:
                particle = particles[idx]
                gm1, gm2, L_1_idx, L_2_idx, ID = particle
                L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
                L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
                
                # Get W values
                W_1, W_2, _, _, _ = get_W(gm1, gm2, L_1, L_2, ID)
                
                if W_1 is not None and W_2 is not None:
                    print(f"  Particle {idx}: Simulating...")
                    
                    # Run simulator
                    sim_passed, _ = evaluate_design(W_1, L_1, W_2, L_2, ID*1e6)
                    
                    if not sim_passed:
                        print(f"    Particle {idx}: REJECTED by simulator")
                        rejected_indices.append(idx)
                        fitness[idx] = np.inf  # Mark as infeasible
                    else:
                        print(f"    Particle {idx}: PASSED simulator")
                else:
                    rejected_indices.append(idx)
                    fitness[idx] = np.inf
            
            # Velocity updates for rejected particles from the simulator
            if len(rejected_indices) > 0:
                print(f"\nPerforming velocity updates for {len(rejected_indices)} rejected particles...")
                
                for idx in rejected_indices:
                    # Try multiple velocity updates
                    for attempt in range(MAX_VELOCITY_UPDATES):
                        offspring, area, specs, success = pso.generate_offspring(idx, particles[idx])
                        
                        if success and area < np.inf:
                            # Check with simulator again
                            gm1, gm2, L_1_idx, L_2_idx, ID = offspring
                            L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
                            L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
                            W_1, W_2, _, _, _ = get_W(gm1, gm2, L_1, L_2, ID)
                            
                            if W_1 is not None and W_2 is not None:
                                sim_passed, _ = evaluate_design(W_1, L_1, W_2, L_2, ID*1e6)
                                
                                if sim_passed:
                                    particles[idx] = offspring
                                    fitness[idx] = area
                                    print(f"    Particle {idx}: Recovered with velocity update (Area={area:.2f})")
                                    break
                    
                    # If still rejected after velocity updates, mark for regeneration
                    if fitness[idx] == np.inf:
                        print(f"    Particle {idx}: Failed all velocity updates")
            
            print("\nUpdating personal and global bests...")
            for i in range(N_PARTICLES):
                if fitness[i] < np.inf and fitness[i] < pso.pbest_fitness[i]:
                    pso.pbest_fitness[i] = fitness[i]
                    pso.pbest_positions[i] = particles[i].copy()
                    print(f"  Particle {i}: Updated pbest = {fitness[i]:.2f} μm²")
            
            best_idx = np.argmin(fitness)
            if fitness[best_idx] < np.inf and fitness[best_idx] < pso.gbest_fitness:
                pso.gbest_fitness = fitness[best_idx]
                pso.gbest_position = particles[best_idx].copy()
                _, _, specs_dict = survivability_test(particles[best_idx])
                pso.gbest_specs = specs_dict
                print(f"  New global best: {fitness[best_idx]:.2f} μm²")
            
            # Refill rejected particles with new random particles
            rejected_mask = fitness == np.inf
            n_rejected = np.sum(rejected_mask)
            
            if n_rejected > 0:
                print(f"\nRefilling {n_rejected} rejected particles...")
                
                refill_count = 0
                for idx in np.where(rejected_mask)[0]:
                    # new particle
                    new_particle, new_area, new_specs = generate_particle(cont_bounds, n_L_values)
                    
                    if new_particle is not None:
                        # Check survivability (already done in generate_particle)
                        particles[idx] = new_particle
                        fitness[idx] = new_area
                        refill_count += 1
                        print(f"    Particle {idx}: Refilled (Area={new_area:.2f})")
                    else:
                        print(f"    Particle {idx}: Failed to refill")
                
                print(f"  Successfully refilled {refill_count}/{n_rejected} particles")
        
        gbest_history.append(pso.gbest_fitness)
        avg_fitness_history.append(np.mean(fitness[fitness < np.inf]))
        
        valid_fitness = fitness[fitness < np.inf]
        print(f"\nIteration {iteration + 1} Summary:")
        print(f"  Global Best: {pso.gbest_fitness:.2f} μm²")
        if len(valid_fitness) > 0:
            print(f"  Average:     {np.mean(valid_fitness):.2f} μm²")
        print(f"  Valid particles: {len(valid_fitness)}/{N_PARTICLES}")
    
    end_time = time.time()
    optimization_time = end_time - start_time
    
    print("Optimization is complete!")
  
    print("\nExtracting final design parameters...")
    
    best_solution = pso.get_best_solution()
    
    gm1 = best_solution['gm1']
    gm2 = best_solution['gm2']
    L_1 = best_solution['L_1']
    L_2 = best_solution['L_2']
    ID = best_solution['ID']
    
    W_1, W_2, _, _, _ = get_W(gm1, gm2, L_1, L_2, ID)
    
    print("\nOptimal Design Parameters:")
    print(f"  gm1     = {gm1*1e6:.2f} μS")
    print(f"  gm2     = {gm2*1e6:.2f} μS")
    print(f"  L_1     = {L_1:.2f} μm")
    print(f"  L_2     = {L_2:.2f} μm")
    print(f"  ID      = {ID*1e6:.2f} μA")
    print(f"  gm/ID_1 = {best_solution['gm_ID_1']:.2f} S/A")
    print(f"  gm/ID_2 = {best_solution['gm_ID_2']:.2f} S/A")
    
    print("\nOptimal Transistor Sizing:")
    print(f"  W_1 = {W_1:.2f} μm")
    print(f"  W_2 = {W_2:.2f} μm")
    print(f"  L_1 = {L_1:.2f} μm")
    print(f"  L_2 = {L_2:.2f} μm")
    
    print(f"\nOPTIMAL AREA: {best_solution['area']:.4f} μm²")

    # Final simulator verification    
    print("\nFinal Simulator Verification...")
    final_check, final_results = evaluate_design(W_1, L_1, W_2, L_2, ID*1e6, plots=True)
    print(f"Final design {'PASSED' if final_check else 'FAILED'} simulator check")
    
    if final_results is not None:
        print("\nPerformance Specifications:")
        print(f"  Slew Rate:    {final_results['SR_meas']*1e-6:.2f} V/μs     (spec: ≥{SR_spec*1e-6:.2f})")
        print(f"  GBW:          {final_results['GBW_meas']*1e-6:.2f} MHz      (spec: ≥{GBW_spec*1e-6:.2f})")
        print(f"  Gain:         {final_results['Gain_meas_dB']:.2f} dB      (spec: ≥{Gain_spec_dB:.2f})")
        print(f"  Phase Margin: {final_results['PM_meas']:.2f}°        (spec: ≥{PM_spec:.2f})")
        print(f"  Power:        {final_results['Power_meas']*1e6:.2f} μW       (spec: ≤{Power_spec*1e6:.2f})")
    
    print(f"\nOptimization Time: {optimization_time:.2f} seconds")
    
    plot_convergence(gbest_history, avg_fitness_history)
    
    save_results(best_solution, W_1, W_2, optimization_time, final_check, final_results)
    
    return best_solution

def plot_convergence(gbest_history, avg_history):

    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(gbest_history, 'b-', linewidth=2, marker='o', markersize=4)
    plt.xlabel('Iteration', fontsize=11)
    plt.ylabel('Global Best Area', fontsize=11)
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

def save_results(best_solution, W_1, W_2, opt_time, sim_passed, results):
    with open('optimization_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("5T OTA OPTIMIZATION RESULTS\n")
        f.write("="*70 + "\n\n")
        
        f.write("DESIGN SPECIFICATIONS:\n")
        f.write(f"  VDD = {VDD} V\n")
        f.write(f"  CL = {CL*1e12:.2f} pF\n")
        f.write(f"  Slew Rate ≥ {SR_spec*1e-6:.2f} V/μs\n")
        f.write(f"  GBW ≥ {GBW_spec*1e-6:.2f} MHz\n")
        f.write(f"  Gain ≥ {Gain_spec_dB:.2f} dB\n")
        f.write(f"  Phase Margin ≥ {PM_spec:.2f}°\n")
        f.write(f"  Power ≤ {Power_spec*1e6:.2f} μW\n\n")
        
        f.write("OPTIMAL DESIGN PARAMETERS:\n")
        f.write(f"  gm1     = {best_solution['gm1']*1e6:.2f} μS\n")
        f.write(f"  gm2     = {best_solution['gm2']*1e6:.2f} μS\n")
        f.write(f"  L_1     = {best_solution['L_1']:.2f} μm\n")
        f.write(f"  L_2     = {best_solution['L_2']:.2f} μm\n")
        f.write(f"  ID      = {best_solution['ID']*1e6:.2f} μA\n")
        f.write(f"  gm/ID_1 = {best_solution['gm_ID_1']:.2f} S/A\n")
        f.write(f"  gm/ID_2 = {best_solution['gm_ID_2']:.2f} S/A\n\n")
        
        f.write("OPTIMAL TRANSISTOR SIZING:\n")
        f.write(f"  W_1 = {W_1:.2f} μm\n")
        f.write(f"  W_2 = {W_2:.2f} μm\n")
        f.write(f"  L_1 = {best_solution['L_1']:.2f} μm\n")
        f.write(f"  L_2 = {best_solution['L_2']:.2f} μm\n\n")
        
        f.write(f"OPTIMAL AREA: {best_solution['area']:.2f} μm²\n\n")
        
        if results is not None:
            f.write("ACHIEVED SPECIFICATIONS:\n")
            f.write(f"  Slew Rate    = {results['SR_meas']*1e-6:.2f} V/μs\n")
            f.write(f"  GBW          = {results['GBW_meas']*1e-6:.2f} MHz\n")
            f.write(f"  Gain         = {results['Gain_meas_dB']:.2f} dB\n")
            f.write(f"  Phase Margin = {results['PM_meas']:.2f}°\n")
            f.write(f"  Power        = {results['Power_meas']*1e6:.2f} μW\n\n")
        
        f.write(f"OPTIMIZATION TIME: {opt_time:.2f} seconds\n")
        f.write(f"FINAL SIMULATOR CHECK: {'PASSED' if sim_passed else 'FAILED'}\n")
    
    print("Results saved to 'optimization_results.txt'")

if __name__ == "__main__":
    results = main()