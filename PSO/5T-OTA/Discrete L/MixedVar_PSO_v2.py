import time
import os
import sys
from contextlib import contextmanager
import numpy as np
import matplotlib.pyplot as plt
from pygmid import Lookup as lk
from scipy.interpolate import interp1d
from scipy.optimize import brentq

NCH = lk('../../../sky130_lookup/simulation/nfet_01v8.mat')
PCH = lk('../../../sky130_lookup/simulation/pfet_01v8.mat')

VDD = 1.8
CL  = 2e-12
SR_spec = 1e6
GBW_spec = 1e6
Gain_spec_dB = 38
Gain_spec = 10**(Gain_spec_dB/20)
PM_spec = 65
Power_spec = 10e-6

L_DISCRETE_VALUES = np.array([0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 
                               0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 
                               0.90, 1.00, 2.00, 3.00])

vgs_sweep = np.arange(0.05, VDD+0.1, 0.01)

def diode_connected_lut(device_data, vgs_sweep):
    L_values = np.unique(device_data['L'])
    diode_lut = {}
    for l_val in L_values:
        gm_id = device_data.lookup('GM_ID', L=l_val, VGS=vgs_sweep, VDS=vgs_sweep, VSB=0)
        diode_lut[l_val] = np.diag(gm_id)
    return diode_lut

nch_results = diode_connected_lut(NCH, vgs_sweep)
pch_results = diode_connected_lut(PCH, vgs_sweep)

@contextmanager
def silence_stdout():
    new_target = open(os.devnull, "w")
    old_target = sys.stdout
    sys.stdout = new_target
    try:
        yield
    finally:
        sys.stdout = old_target
        new_target.close()

def get_W(gm1, gm2, L_1, L_2, ID):
    gm_ID_1 = gm1 / ID
    gm_ID_2 = gm2 / ID

    with silence_stdout():
        try:
            Vgs_2 = PCH.lookupVGS(GM_ID=gm_ID_2, VSB=0, L=L_2)
            Vgs_2 = PCH.lookupVGS(GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
        
            JD_1 = NCH.lookup('ID_W', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
            JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

            W_1 = ID / JD_1
            W_2 = ID / JD_2
        except:
            return None, None

    return W_1, W_2

def get_specVars(gm1, gm2, L_1, L_2, ID):
    gm_ID_1 = gm1 / ID
    gm_ID_2 = gm2 / ID

    with silence_stdout():
        try:
            Vgs_2 = PCH.lookupVGS(GM_ID=gm_ID_2, VSB=0, L=L_2)
            Vgs_2 = PCH.lookupVGS(GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

            Cdd_1 = gm1 / NCH.lookup('GM_CDD', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
            Cdd_2 = gm2 / PCH.lookup('GM_CDD', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
            Cpar = Cdd_1 + Cdd_2

            Cgg_2 = gm2 / PCH.lookup('GM_CGG', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
            Cx = Cpar + Cgg_2

            JD_1 = NCH.lookup('ID_W', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
            JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

            W_1 = ID / JD_1
            W_2 = ID / JD_2

            gds_1 = gm1 / NCH.lookup('GM_GDS', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
            gds_2 = gm2 / PCH.lookup('GM_GDS', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
        except:
            return None, None, None, None, None, None

    return Cx, Cpar, W_1, W_2, gds_1, gds_2

def get_feasRegion(gm_ID, L_discrete_values, SR_spec, CL, Power_spec, GBW_spec):
    gm_ID_min = gm_ID[0]
    gm_ID_max = gm_ID[1]

    ID_min = SR_spec * CL / 2
    ID_max = Power_spec / VDD / 2

    gm1_min_GBW = 2 * np.pi * GBW_spec * CL
    gm1_min_gmID = gm_ID_min * ID_min
    gm1_min = max(gm1_min_GBW, gm1_min_gmID)
    gm1_max = gm_ID_max * ID_max

    gm2_min = gm_ID_min * ID_min
    gm2_max = gm_ID_max * ID_max

    L_available = L_discrete_values
    n_L_values = len(L_available)

    return gm1_min, gm1_max, gm2_min, gm2_max, L_available, n_L_values, ID_min, ID_max

def survivability_test(particle, verbose=False):
    """
    Test if a particle meets all design specifications
    particle = [gm1, gm2, L_1_idx, L_2_idx, ID]
    """
    gm1, gm2, L_1_idx, L_2_idx, ID = particle
    
    L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
    L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
    
    result = get_specVars(gm1, gm2, L_1, L_2, ID)
    
    if result[0] is None:
        return False, np.inf, None
    
    Cx, Cpar, W_1, W_2, gds_1, gds_2 = result
    
    Cload_total = CL + Cpar
    
    SR_calc = (ID * 2) / Cload_total
    
    GBW_calc = gm1 / (2 * np.pi * Cload_total)
    
    Gain_calc = gm1 / (gds_1 + gds_2)
    
    PM_calc = 90 - (np.arctan(GBW_calc / (gm2 / Cx)) * (180/np.pi))
    
    Power_calc = ID * 2 * VDD
    
    Area_active = 2 * ((W_1 * L_1) + (W_2 * L_2))
    
    specs_met = (
        SR_calc >= SR_spec and
        GBW_calc >= GBW_spec and
        Gain_calc >= Gain_spec and
        PM_calc >= PM_spec and
        Power_calc <= Power_spec and
        W_1 > 0.42 and W_2 > 0.42 and
        gm1/ID >= 3 and gm1/ID <= 20 and
        gm2/ID >= 3 and gm2/ID <= 20 and
        Area_active > 0
    )
    
    specs_dict = {
        'SR': SR_calc,
        'GBW': GBW_calc,
        'Gain': Gain_calc,
        'Gain_dB': 20*np.log10(Gain_calc),
        'PM': PM_calc,
        'Power': Power_calc,
        'Area': Area_active,
        'W_1': W_1,
        'W_2': W_2,
        'L_1': L_1,
        'L_2': L_2
    }
    
    if verbose and specs_met:
        print(f"  SR: {SR_calc*1e-6:.2f} V/μs (spec: {SR_spec*1e-6:.2f})")
        print(f"  GBW: {GBW_calc*1e-6:.2f} MHz (spec: {GBW_spec*1e-6:.2f})")
        print(f"  Gain: {20*np.log10(Gain_calc):.2f} dB (spec: {Gain_spec_dB:.2f})")
        print(f"  PM: {PM_calc:.2f}° (spec: {PM_spec:.2f})")
        print(f"  Power: {Power_calc*1e6:.2f} μW (spec: {Power_spec*1e6:.2f})")
        print(f"  Area: {Area_active:.2f} μm²")
    
    return specs_met, Area_active, specs_dict

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

class HybridMixedPSO:
    
    def __init__(self, cont_bounds, n_L_values, n_particles=50, max_iterations=100,
                 w_max=0.8, w_min=0.5, c1=1.7, c2=1.7, max_velocity_updates=5):
        
        self.cont_bounds = cont_bounds
        self.n_L_values = n_L_values
        self.n_particles = n_particles
        self.max_iterations = max_iterations
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.max_velocity_updates = max_velocity_updates
        
        self.continuous_indices = [0, 1, 4]
        self.discrete_indices = [2, 3]
        self.n_cont = len(self.continuous_indices)
        self.n_disc = len(self.discrete_indices)
        
        self.positions = np.zeros((n_particles, 5))
        self.velocities = np.zeros((n_particles, self.n_cont))
        self.fitness = np.full(n_particles, np.inf)
        self.pbest_positions = np.zeros((n_particles, 5))
        self.pbest_fitness = np.full(n_particles, np.inf)
        self.gbest_position = np.zeros(5)
        self.gbest_fitness = np.inf
        self.gbest_specs = None
        
        self.w_bar = 0.5
        self.alpha_bar = 0.5
        self.param_set = []
        self.S = 0
        
        self.discrete_probs = np.ones((self.n_disc, n_L_values)) / n_L_values
        
        self.fitness_history = []
        self.gbest_history = []
        
    def initialize_swarm(self):
        print("Initializing swarm...")
        successful_particles = 0
        
        for i in range(self.n_particles):
            particle, area, specs = generate_particle(self.cont_bounds, self.n_L_values)
            
            if particle is not None:
                self.positions[i] = particle
                self.fitness[i] = area
                self.pbest_positions[i] = particle.copy()
                self.pbest_fitness[i] = area
                
                if area < self.gbest_fitness:
                    self.gbest_fitness = area
                    self.gbest_position = particle.copy()
                    self.gbest_specs = specs
                
                successful_particles += 1
                print(f"  Particle {i+1}/{self.n_particles}: Area = {area:.2f} μm²")
            else:
                print(f"  Particle {i+1}/{self.n_particles}: Failed to generate valid particle")
        
        for i, cont_idx in enumerate(self.continuous_indices):
            bound_range = self.cont_bounds[i][1] - self.cont_bounds[i][0]
            self.velocities[:, i] = np.random.uniform(
                -0.1 * bound_range,
                0.1 * bound_range,
                self.n_particles
            )
        
        print(f"\nInitialization: {successful_particles}/{self.n_particles} valid particles")
        print(f"Initial global best: {self.gbest_fitness:.2f} μm²\n")
        
        return successful_particles > 0
    
    def adaptive_parameter_tuning(self):
        rand = np.random.random()
        
        if rand <= 0.5:
            w = np.random.standard_cauchy() * 0.1 + self.w_bar
            alpha = np.random.standard_cauchy() * 0.1 + self.alpha_bar
        else:
            w = np.random.normal(self.w_bar, 0.1)
            alpha = np.random.normal(self.alpha_bar, 0.1)
        
        w = np.clip(w, 0.4, 0.9)
        alpha = np.clip(alpha, 0.0, 1.0)
        
        return w, alpha
    
    def update_parameters(self, w, alpha):
        self.param_set.append((w, alpha))
        self.S += 1
        
        self.w_bar = (self.w_bar * (self.S - 1) + w) / self.S
        self.alpha_bar = (self.alpha_bar * (self.S - 1) + alpha) / self.S
    
    def update_discrete_probabilities(self, alpha):
        sorted_indices = np.argsort(self.pbest_fitness)
        
        superior_half = sorted_indices[self.n_particles//2:]
        
        for var_idx in range(self.n_disc):
            disc_idx = self.discrete_indices[var_idx]
            
            counts = np.zeros(self.n_L_values)
            for sup_idx in superior_half:
                value_idx = int(self.pbest_positions[sup_idx, disc_idx])
                counts[value_idx] += 1
            
            historical_prob = self.discrete_probs[var_idx, :]
            current_prob = counts / len(superior_half)
            
            self.discrete_probs[var_idx, :] = (
                alpha * historical_prob + (1 - alpha) * current_prob
            )
            
            prob_sum = np.sum(self.discrete_probs[var_idx, :])
            if prob_sum > 0:
                self.discrete_probs[var_idx, :] /= prob_sum
            else:
                self.discrete_probs[var_idx, :] = 1.0 / self.n_L_values
    
    def continuous_reproduction(self, particle_idx, w, iteration):
        new_cont_vars = np.zeros(self.n_cont)
        
        for i, cont_idx in enumerate(self.continuous_indices):
            r1 = np.random.random()
            r2 = np.random.random()
            
            current_pos = self.positions[particle_idx, cont_idx]
            pbest_pos = self.pbest_positions[particle_idx, cont_idx]
            gbest_pos = self.gbest_position[cont_idx]
            
            cognitive = self.c1 * r1 * (pbest_pos - current_pos)
            social = self.c2 * r2 * (gbest_pos - current_pos)
            
            self.velocities[particle_idx, i] = (
                w * self.velocities[particle_idx, i] + cognitive + social
            )
            
            new_cont_vars[i] = current_pos + self.velocities[particle_idx, i]
            
            new_cont_vars[i] = np.clip(
                new_cont_vars[i],
                self.cont_bounds[i][0],
                self.cont_bounds[i][1]
            )
        
        return new_cont_vars
    
    def discrete_reproduction(self, particle_idx):
        new_disc_vars = np.zeros(self.n_disc)
        
        for var_idx in range(self.n_disc):
            probs = self.discrete_probs[var_idx, :]
            new_disc_vars[var_idx] = np.random.choice(self.n_L_values, p=probs)
        
        return new_disc_vars
    
    def generate_offspring(self, particle_idx, w, iteration):
        for attempt in range(self.max_velocity_updates):
            new_cont_vars = self.continuous_reproduction(particle_idx, w, iteration)
            
            new_disc_vars = self.discrete_reproduction(particle_idx)
            
            offspring = np.zeros(5)
            offspring[self.continuous_indices] = new_cont_vars
            offspring[self.discrete_indices] = new_disc_vars
            
            passed, area, specs = survivability_test(offspring)
            
            if passed:
                return offspring, area, specs, True
        
        particle, area, specs = generate_particle(self.cont_bounds, self.n_L_values)
        
        if particle is not None:
            return particle, area, specs, False
        else:
            return self.positions[particle_idx], self.fitness[particle_idx], None, False
    
    def optimize(self):
        
        if not self.initialize_swarm():
            print("ERROR: Failed to initialize swarm!")
            return None
        
        for iteration in range(self.max_iterations):
            print(f"\nITERATION {iteration + 1}/{self.max_iterations}")
            print("-" * 70)
            
            w_linear = self.w_min + (self.w_max - self.w_min) * (self.max_iterations - iteration) / self.max_iterations
            
            w_adaptive, alpha = self.adaptive_parameter_tuning()
            
            self.update_discrete_probabilities(alpha)


            # change to see what is good: adaptive or linear
            for i in range(self.n_particles):
                offspring, area, specs, from_reproduction = self.generate_offspring(i, w_adaptive, iteration)
                
                if area < self.fitness[i]:
                    self.positions[i] = offspring
                    self.fitness[i] = area
                
                if area < self.pbest_fitness[i]:
                    self.pbest_fitness[i] = area
                    self.pbest_positions[i] = offspring.copy()
                    
                    if from_reproduction:
                        self.update_parameters(w_adaptive, alpha)
                
                if area < self.gbest_fitness:
                    self.gbest_fitness = area
                    self.gbest_position = offspring.copy()
                    self.gbest_specs = specs
                    print(f" New global best Area = {area:.2f} μm²")
            
            self.fitness_history.append(self.fitness.copy())
            self.gbest_history.append(self.gbest_fitness)
            
            avg_fitness = np.mean(self.fitness)
            print(f"\n  Global Best: {self.gbest_fitness:.2f} μm²")
            print(f"  Average: {avg_fitness:.2f} μm²")
            print(f"  w={self.w_bar:.3f}, ᾱ={self.alpha_bar:.3f}")
            
            if iteration % 10 == 0:
                print(f"\n  Discrete Probabilities (L_1, L_2):")
                for var_idx in range(self.n_disc):
                    top_3_indices = np.argsort(self.discrete_probs[var_idx, :])[-3:][::-1]
                    top_3_probs = self.discrete_probs[var_idx, top_3_indices]
                    top_3_values = L_DISCRETE_VALUES[top_3_indices]
                    print(f"    Var {var_idx}: Top 3: {[(v, f'{p:.3f}') for v, p in zip(top_3_values, top_3_probs)]}")
        
        return self.get_results()
    
    
    def get_results(self):
        gm1, gm2, L_1_idx, L_2_idx, ID = self.gbest_position
        L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
        L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
        
        W_1, W_2 = get_W(gm1, gm2, L_1, L_2, ID)
        
        results = {
            'optimal_particle': {
                'gm1': gm1,
                'gm2': gm2,
                'L_1': L_1,
                'L_2': L_2,
                'ID': ID,
                'gm_ID_1': gm1/ID,
                'gm_ID_2': gm2/ID
            },
            'optimal_sizing': {
                'W_1': W_1,
                'W_2': W_2,
                'L_1': L_1,
                'L_2': L_2
            },
            'optimal_area': self.gbest_fitness,
            'specifications': self.gbest_specs,
            'convergence_history': self.gbest_history,
            'discrete_probs_final': self.discrete_probs.copy()
        }
        
        return results
    
    def plot_convergence(self, save_path='pso_hybrid_mixed_convergence.png'):
        fig = plt.figure(figsize=(16, 5))
        
        plt.subplot(1, 4, 1)
        plt.plot(self.gbest_history, 'b-', linewidth=2, marker='o', markersize=4)
        plt.xlabel('Iteration', fontsize=11)
        plt.ylabel('Global Best Area (μm²)', fontsize=11)
        plt.title('Convergence - Global Best', fontsize=12, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 4, 2)
        fitness_array = np.array(self.fitness_history)
        avg_fitness = np.mean(fitness_array, axis=1)
        std_fitness = np.std(fitness_array, axis=1)
        
        iterations = range(len(avg_fitness))
        plt.plot(iterations, avg_fitness, 'g-', linewidth=2, label='Average')
        plt.fill_between(iterations, 
                        avg_fitness - std_fitness, 
                        avg_fitness + std_fitness, 
                        alpha=0.3, color='g', label='±1 Std Dev')
        plt.plot(self.gbest_history, 'r--', linewidth=2, label='Global Best')
        plt.xlabel('Iteration', fontsize=11)
        plt.ylabel('Area (μm²)', fontsize=11)
        plt.title('Swarm Statistics', fontsize=12, fontweight='bold')
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 4, 3)
        if len(self.param_set) > 0:
            w_history = [p[0] for p in self.param_set]
            alpha_history = [p[1] for p in self.param_set]
            plt.plot(w_history, 'b-', alpha=0.3, linewidth=1, label='w samples')
            plt.plot(alpha_history, 'r-', alpha=0.3, linewidth=1, label='α samples')
            plt.axhline(y=self.w_bar, color='b', linestyle='--', linewidth=2, label=f'w̄={self.w_bar:.3f}')
            plt.axhline(y=self.alpha_bar, color='r', linestyle='--', linewidth=2, label=f'ᾱ={self.alpha_bar:.3f}')
        plt.xlabel('Successful Update', fontsize=11)
        plt.ylabel('Parameter Value', fontsize=11)
        plt.title('Adaptive Parameters', fontsize=12, fontweight='bold')
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 4, 4)
        x_pos = np.arange(len(L_DISCRETE_VALUES))
        width = 0.35
        plt.bar(x_pos - width/2, self.discrete_probs[0, :], width, label='L_1', alpha=0.7)
        plt.bar(x_pos + width/2, self.discrete_probs[1, :], width, label='L_2', alpha=0.7)
        plt.xlabel('L value index', fontsize=11)
        plt.ylabel('Probability', fontsize=11)
        plt.title('Final Discrete Probabilities', fontsize=12, fontweight='bold')
        plt.xticks(x_pos, [f'{L_DISCRETE_VALUES[i]:.2f}' for i in range(len(L_DISCRETE_VALUES))], 
                   rotation=45, fontsize=8)
        plt.legend(fontsize=9)
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nConvergence plot saved to {save_path}")

def main():
    
    gm_ID_range = (3, 20)
    
    gm1_min, gm1_max, gm2_min, gm2_max, L_available, n_L_values, ID_min, ID_max = \
        get_feasRegion(gm_ID_range, L_DISCRETE_VALUES, SR_spec, CL, Power_spec, GBW_spec)
    
    cont_bounds = [
        (gm1_min, gm1_max),
        (gm2_min, gm2_max),
        (ID_min, ID_max)
    ]
    
    print("\n" + "-"*70)
    print("FEASIBLE REGION:")
    print("-"*70)
    print(f"Continuous Variables:")
    print(f"  gm1: [{gm1_min*1e6:.2f}, {gm1_max*1e6:.2f}] μS")
    print(f"  gm2: [{gm2_min*1e6:.2f}, {gm2_max*1e6:.2f}] μS")
    print(f"  ID:  [{ID_min*1e6:.2f}, {ID_max*1e6:.2f}] μA")
    print(f"\nDiscrete Variables:")
    print(f"  L_1, L_2 in {{{', '.join([f'{v:.2f}' for v in L_available])}}} μm")
    print(f"  Total discrete values: {n_L_values}")
    print("-"*70 + "\n")
    
    start_time = time.time()
    
    pso = HybridMixedPSO(
        cont_bounds=cont_bounds,
        n_L_values=n_L_values,
        n_particles=50,
        max_iterations=100,
        w_max=0.8,
        w_min=0.5,
        c1=1.7,
        c2=1.7,
        max_velocity_updates=5
    )
    
    results = pso.optimize()
    
    end_time = time.time()
    
    if results:
        print("\n" + "="*70)
        print("OPTIMIZATION RESULTS")
        print("="*70)
        
        print("\nOptimal Design Parameters:")
        print(f"  gm1     = {results['optimal_particle']['gm1']*1e6:.4f} μS")
        print(f"  gm2     = {results['optimal_particle']['gm2']*1e6:.4f} μS")
        print(f"  L_1     = {results['optimal_particle']['L_1']:.2f} μm  (discrete)")
        print(f"  L_2     = {results['optimal_particle']['L_2']:.2f} μm  (discrete)")
        print(f"  ID      = {results['optimal_particle']['ID']*1e6:.4f} μA")
        print(f"  gm/ID_1 = {results['optimal_particle']['gm_ID_1']:.2f} S/A")
        print(f"  gm/ID_2 = {results['optimal_particle']['gm_ID_2']:.2f} S/A")
        
        print("\nOptimal Transistor Sizing:")
        print(f"  W_1 = {results['optimal_sizing']['W_1']:.4f} μm")
        print(f"  W_2 = {results['optimal_sizing']['W_2']:.4f} μm")
        print(f"  L_1 = {results['optimal_sizing']['L_1']:.2f} μm")
        print(f"  L_2 = {results['optimal_sizing']['L_2']:.2f} μm")
        
        print(f"\n OPTIMAL AREA: {results['optimal_area']:.4f} μm²")
        
        print("\nPerformance Specifications:")
        specs = results['specifications']
        print(f"  Slew Rate:    {specs['SR']*1e-6:.2f} V/μs    (spec: ≥{SR_spec*1e-6:.2f})")
        print(f"  GBW:          {specs['GBW']*1e-6:.2f} MHz     (spec: ≥{GBW_spec*1e-6:.2f})")
        print(f"  Gain:         {specs['Gain_dB']:.2f} dB      (spec: ≥{Gain_spec_dB:.2f})")
        print(f"  Phase Margin: {specs['PM']:.2f}°        (spec: ≥{PM_spec:.2f})")
        print(f"  Power:        {specs['Power']*1e6:.2f} μW      (spec: ≤{Power_spec*1e6:.2f})")
        
        print(f"\nOptimization Time: {end_time - start_time:.2f} seconds")
        print("="*70 + "\n")
        
        pso.plot_convergence('pso_hybrid_mixed_convergence.png')
        save_results_to_file(results, end_time - start_time)
        
    else:
        print("\n Optimization failed!")
    
    return results

def save_results_to_file(results, opt_time):
    """Save detailed results to file"""
    with open('pso_hybrid_mixed_results.txt', 'w', encoding='utf-8') as f:
        

        f.write("DESIGN SPECIFICATIONS:\n")
        f.write(f"  VDD = {VDD} V\n")
        f.write(f"  CL = {CL*1e12:.2f} pF\n")
        f.write(f"  Slew Rate ≥ {SR_spec*1e-6:.2f} V/μs\n")
        f.write(f"  GBW ≥ {GBW_spec*1e-6:.2f} MHz\n")
        f.write(f"  Gain ≥ {Gain_spec_dB:.2f} dB\n")
        f.write(f"  Phase Margin ≥ {PM_spec:.2f}°\n")
        f.write(f"  Power ≤ {Power_spec*1e6:.2f} μW\n\n")
        
        f.write("VARIABLE TYPES:\n")
        f.write(f"  Continuous: gm1, gm2, ID\n")
        f.write(f"  Discrete: L_1, L_2 ∈ {{{', '.join([f'{v:.2f}' for v in L_DISCRETE_VALUES])}}} μm\n\n")
        
        f.write("OPTIMAL DESIGN PARAMETERS:\n")
        f.write(f"  gm1     = {results['optimal_particle']['gm1']*1e6:.6f} μS\n")
        f.write(f"  gm2     = {results['optimal_particle']['gm2']*1e6:.6f} μS\n")
        f.write(f"  L_1     = {results['optimal_particle']['L_1']:.2f} μm\n")
        f.write(f"  L_2     = {results['optimal_particle']['L_2']:.2f} μm\n")
        f.write(f"  ID      = {results['optimal_particle']['ID']*1e6:.6f} μA\n")
        f.write(f"  gm/ID_1 = {results['optimal_particle']['gm_ID_1']:.6f} S/A\n")
        f.write(f"  gm/ID_2 = {results['optimal_particle']['gm_ID_2']:.6f} S/A\n\n")
        
        f.write("OPTIMAL TRANSISTOR SIZING:\n")
        f.write(f"  W_1 = {results['optimal_sizing']['W_1']:.6f} μm\n")
        f.write(f"  W_2 = {results['optimal_sizing']['W_2']:.6f} μm\n")
        f.write(f"  L_1 = {results['optimal_sizing']['L_1']:.2f} μm\n")
        f.write(f"  L_2 = {results['optimal_sizing']['L_2']:.2f} μm\n\n")
        
        f.write(f"OPTIMAL AREA: {results['optimal_area']:.6f} μm²\n\n")
        
        f.write("ACHIEVED SPECIFICATIONS:\n")
        specs = results['specifications']
        f.write(f"  Slew Rate    = {specs['SR']*1e-6:.6f} V/μs\n")
        f.write(f"  GBW          = {specs['GBW']*1e-6:.6f} MHz\n")
        f.write(f"  Gain         = {specs['Gain_dB']:.6f} dB\n")
        f.write(f"  Phase Margin = {specs['PM']:.6f}°\n")
        f.write(f"  Power        = {specs['Power']*1e6:.6f} μW\n\n")
        
        f.write(f"OPTIMIZATION TIME: {opt_time:.2f} seconds\n")
    
    print("Results saved to pso_hybrid_mixed_results.txt")

if __name__ == "__main__":
    results = main()
