import time
import os
import sys
from contextlib import contextmanager
import numpy as np
import matplotlib.pyplot as plt
from pygmid import Lookup as lk
from scipy.interpolate import interp1d
from scipy.optimize import brentq

NCH = lk('../../sky130_lookup/simulation/nfet_01v8.mat')
PCH = lk('../../sky130_lookup/simulation/pfet_01v8.mat')

# ===================
# 5T-OTA DESIGN SPECS
# ===================
VDD = 1.8                           # Supply Voltage (V)
CL  = 2e-12                         # Load Capacitance (F)
SR_spec = 1e6                       # Slew Rate (V/s)
GBW_spec = 1e6                      # Gain Bandwidth (Hz)
Gain_spec_dB = 38                   # DC Gain (dB)
Gain_spec = 10**(Gain_spec_dB/20)   # Convert dB to V/V
PM_spec = 65                        # Phase Margin (degrees)
Power_spec = 10e-6                  # Power Consumption (W)

# ===============================
# LUT FOR DIODE CONNECTED DEVICES
# ===============================
vgs_sweep = np.arange(0.05, VDD+0.1, 0.01)

# Function to create diode-connected LUT
def diode_connected_lut(device_data, vgs_sweep):
    L_values = np.unique(device_data['L'])
    diode_lut = {}

    for l_val in L_values:
        gm_id = device_data.lookup('GM_ID', L=l_val, VGS=vgs_sweep, VDS=vgs_sweep, VSB=0)
        diode_lut[l_val] = np.diag(gm_id)

    return diode_lut

# Create LUTs for diode-connected NMOS and PMOS
nch_results = diode_connected_lut(NCH, vgs_sweep)
pch_results = diode_connected_lut(PCH, vgs_sweep)

# Function to get VGS for a target gm/ID
def getVGS_diode(device_type, target_gm_id, length):
    if device_type.lower() == 'nmos':
        gm_id_vec = nch_results[length]
    elif device_type.lower() == 'pmos':
        gm_id_vec = pch_results[length]
    else:
        raise ValueError("Device type must be 'nmos' or 'pmos'.")

    get_vgs = interp1d(gm_id_vec, vgs_sweep, kind='linear', bounds_error=False)
    vgs_required = get_vgs(target_gm_id)
    return vgs_required
# ===============================

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

def vgs_error(vgs_guess, target_gm_id, L, VSB):  # VGS solver function
    with silence_stdout():
        vgs_calculated = PCH.lookupVGS(GM_ID=target_gm_id, VDS=vgs_guess, VSB=VSB, L=L)
    return vgs_guess - vgs_calculated

def get_W(gm1, gm2, L_1, L_2, ID):
    gm_ID_1 = gm1 / ID
    gm_ID_2 = gm2 / ID

    try:
        Vgs_2 = brentq(vgs_error, 0.3, 1.8, args=(gm_ID_2, L_2, 0))
    except ValueError:
        return None, None
    # Vgs_2 = getVGS_diode('PMOS', gm_ID_2, L_2)

    with silence_stdout():
        JD_1 = NCH.lookup('ID_W', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
        JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

        W_1 = ID / JD_1
        W_2 = ID / JD_2

    return W_1, W_2

def get_specVars(gm1, gm2, L_1, L_2, ID):
    gm_ID_1 = gm1 / ID
    gm_ID_2 = gm2 / ID

    try:
        Vgs_2 = brentq(vgs_error, 0.3, 1.8, args=(gm_ID_2, L_2, 0))
    except ValueError:
        return None, None, None, None, None, None
    # Vgs_2 = getVGS_diode('PMOS', gm_ID_2, L_2)

    with silence_stdout():
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

    return Cx, Cpar, W_1, W_2, gds_1, gds_2

def get_feasRegion(gm_ID, L_1, L_2, SR_spec, CL, Power_spec, GBW_spec):
    gm_ID_min = gm_ID[0]
    gm_ID_max = gm_ID[1]

    ID_min = SR_spec * CL / 2  # Minimum current (A)
    ID_max = Power_spec / VDD / 2  # Maximum tail current (A)

    gm1_min_GBW = 2 * np.pi * GBW_spec * CL  # Minimum gm1 for GBW spec
    gm1_min_gmID = gm_ID_min * ID_min  # Minimum gm1 for gm/ID
    gm1_min = max(gm1_min_GBW, gm1_min_gmID)  # Overall minimum gm1
    gm1_max = gm_ID_max * ID_max  # Maximum gm1 for gm/ID

    gm2_min = gm_ID_min * ID_min  # Minimum gm2 for gm/ID
    gm2_max = gm_ID_max * ID_max  # Maximum gm2 for gm/ID

    L_1_min = L_1[0]
    L_1_max = L_1[1]

    L_2_min = L_2[0]
    L_2_max = L_2[1]

    return gm1_min, gm1_max, gm2_min, gm2_max, L_1_min, L_1_max, L_2_min, L_2_max, ID_min, ID_max

# We can check the feasibility
def survivability_test(particle, verbose=False):
    """
    This is to test if a particle meets all design specifications
    particle = [gm1, gm2, L_1, L_2, ID]
    """
    gm1, gm2, L_1, L_2, ID = particle
    
    # Get circuit parameters
    result = get_specVars(gm1, gm2, L_1, L_2, ID)
    
    if result[0] is None:  # Check if calculations failed
        return False, np.inf, None
    
    Cx, Cpar, W_1, W_2, gds_1, gds_2 = result
    

    Cload_total = CL + Cpar
    
    # Slew Rate
    SR_calc = (ID * 2) / Cload_total
    
    # Gain Bandwidth
    GBW_calc = gm1 / (2 * np.pi * Cload_total)
    
    # Gain
    Gain_calc = gm1 / (gds_1 + gds_2)
    
    # Phase Margin
    PM_calc = 90 - (np.arctan(GBW_calc / (gm2 / Cx)) * (180/np.pi))
    
    # Power Consumption
    Power_calc = ID * 2 * VDD
    
    # Active area calculation
    Area_active = 2 * ((W_1 * L_1) + (W_2 * L_2))
    
    # Check all constraints
    specs_met = (
        SR_calc >= SR_spec and
        GBW_calc >= GBW_spec and
        Gain_calc >= Gain_spec and
        PM_calc >= PM_spec and
        Power_calc <= Power_spec and
        W_1 > 0.42 and W_2 > 0.42 and
        gm1/ID >= 3 and gm1/ID <= 20 and
        gm2/ID >= 3 and gm2/ID <= 20 and
        L_1 >= 0.15 and L_1 <= 3 and
        L_2 >= 0.15 and L_2 <= 3 and
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
        'W_2': W_2
    }
    
    if verbose and specs_met:
        print(f"  SR: {SR_calc*1e-6:.2f} V/μs (spec: {SR_spec*1e-6:.2f})")
        print(f"  GBW: {GBW_calc*1e-6:.2f} MHz (spec: {GBW_spec*1e-6:.2f})")
        print(f"  Gain: {20*np.log10(Gain_calc):.2f} dB (spec: {Gain_spec_dB:.2f})")
        print(f"  PM: {PM_calc:.2f}° (spec: {PM_spec:.2f})")
        print(f"  Power: {Power_calc*1e6:.2f} μW (spec: {Power_spec*1e6:.2f})")
        print(f"  Area: {Area_active:.2f} μm²")
    
    return specs_met, Area_active, specs_dict


# Generate particles for PSO
def generate_particle(bounds, max_attempts=1000):
    """
    bounds = [gm1_bounds, gm2_bounds, L1_bounds, L2_bounds, ID_bounds]
    """
    for attempt in range(max_attempts):
        particle = np.array([
            np.random.uniform(bounds[0][0], bounds[0][1]),  # gm1
            np.random.uniform(bounds[1][0], bounds[1][1]),  # gm2
            np.random.uniform(bounds[2][0], bounds[2][1]),  # L_1
            np.random.uniform(bounds[3][0], bounds[3][1]),  # L_2
            np.random.uniform(bounds[4][0], bounds[4][1])   # ID
        ])
        
        # Test feasibility
        passed, area, specs = survivability_test(particle)
        
        if passed:
            return particle, area, specs
    
    # If we reach here, couldn't generate valid particle
    return None, np.inf, None

# ===================================
# HYBRID-PSO ALGORITHM IMPLEMENTATION
# ===================================
class HybridPSO:
    def __init__(self, bounds, n_particles=50, max_iterations=100, 
                 w_max=0.8, w_min=0.5, c1=1.7, c2=1.7, max_velocity_updates=5):

        self.bounds = bounds
        self.n_particles = n_particles
        self.max_iterations = max_iterations
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.max_velocity_updates = max_velocity_updates
        
        # Initialize swarm
        self.positions = np.zeros((n_particles, 5))  # [gm1, gm2, L_1, L_2, ID]
        self.velocities = np.zeros((n_particles, 5))
        self.fitness = np.full(n_particles, np.inf)
        self.pbest_positions = np.zeros((n_particles, 5))
        self.pbest_fitness = np.full(n_particles, np.inf)
        self.gbest_position = np.zeros(5)
        self.gbest_fitness = np.inf
        self.gbest_specs = None
        
        # History tracking
        self.fitness_history = []
        self.gbest_history = []
        
    def initialize_swarm(self):
        """Generate initial swarm using particle generation function"""
        print("Initializing swarm...")
        successful_particles = 0
        
        for i in range(self.n_particles):
            particle, area, specs = generate_particle(self.bounds)
            
            if particle is not None:
                self.positions[i] = particle
                self.fitness[i] = area
                self.pbest_positions[i] = particle.copy()
                self.pbest_fitness[i] = area
                
                # Update global best
                if area < self.gbest_fitness:
                    self.gbest_fitness = area
                    self.gbest_position = particle.copy()
                    self.gbest_specs = specs
                
                successful_particles += 1
                print(f"  Particle {i+1}/{self.n_particles}: Area = {area:.2f} μm²")
            else:
                print(f"  Particle {i+1}/{self.n_particles}: Failed to generate valid particle")
        
        # Initialize velocities (small random values)
        velocity_scale = 0.1
        for i in range(5):
            bound_range = self.bounds[i][1] - self.bounds[i][0]
            self.velocities[:, i] = np.random.uniform(
                -velocity_scale * bound_range,
                velocity_scale * bound_range,
                self.n_particles
            )
        
        print(f"\nInitialization complete: {successful_particles}/{self.n_particles} valid particles")
        print(f"Initial global best area: {self.gbest_fitness:.2f} μm²\n")
        
        return successful_particles > 0
    
    def update_particle(self, idx, iteration):
        """Update velocity and position of a single particle with multiple attempts"""
        
        for attempt in range(self.max_velocity_updates):
            # Update velocity
            r1 = np.random.random(5)
            r2 = np.random.random(5)
            
            # Current inertia weight (linearly decreasing - as in H. PSO)
            w = self.w_min + (self.w_max - self.w_min) * (self.max_iterations - iteration) / self.max_iterations
            
            cognitive = self.c1 * r1 * (self.pbest_positions[idx] - self.positions[idx])
            social = self.c2 * r2 * (self.gbest_position - self.positions[idx])
            
            self.velocities[idx] = w * self.velocities[idx] + cognitive + social
            
            new_position = self.positions[idx] + self.velocities[idx]
            
            # Clamp to bounds
            for i in range(5):
                new_position[i] = np.clip(new_position[i], self.bounds[i][0], self.bounds[i][1])
            
            # Test feasibility
            passed, area, specs = survivability_test(new_position)
            
            if passed:
                self.positions[idx] = new_position
                self.fitness[idx] = area
                
                # Find the local best (personal to one swarm)
                if area < self.pbest_fitness[idx]:
                    self.pbest_fitness[idx] = area
                    self.pbest_positions[idx] = new_position.copy()
                
                # Update global best
                if area < self.gbest_fitness:
                    self.gbest_fitness = area
                    self.gbest_position = new_position.copy()
                    self.gbest_specs = specs
                    print(f"    New global best! Area = {area:.2f} μm²")
                
                return True
        
        # If all attempts failed, generate new particle
        print(f"    Particle {idx+1}: Failed after {self.max_velocity_updates} attempts, generating new particle...")
        new_particle, area, specs = generate_particle(self.bounds)
        
        if new_particle is not None:
            self.positions[idx] = new_particle
            self.fitness[idx] = area
            
            if area < self.pbest_fitness[idx]:
                self.pbest_fitness[idx] = area
                self.pbest_positions[idx] = new_particle.copy()
            
            if area < self.gbest_fitness:
                self.gbest_fitness = area
                self.gbest_position = new_particle.copy()
                self.gbest_specs = specs
                print(f"    New global best! Area = {area:.2f} μm²")
            
            return True
        
        return False
    
    def optimize(self):
       
        # Initialize swarm
        if not self.initialize_swarm():
            print("ERROR: Failed to initialize swarm!")
            return None
        
        # Main iteration loop
        for iteration in range(self.max_iterations):
            print(f"ITERATION {iteration + 1}/{self.max_iterations}")

            
            for i in range(self.n_particles):
                self.update_particle(i, iteration)
            

            self.fitness_history.append(self.fitness.copy())
            self.gbest_history.append(self.gbest_fitness)
            
            # Print iteration summary
            avg_fitness = np.mean(self.fitness)
            print(f"\nIteration {iteration + 1} Summary:")
            print(f"  Global Best Area: {self.gbest_fitness:.2f} μm²")
            print(f"  Average Area: {avg_fitness:.2f} μm²")
            print(f"  Best Particle: {np.argmin(self.fitness) + 1}")
            
            # # Early stopping if converged
            # if iteration > 10:
            #     recent_improvement = self.gbest_history[-10] - self.gbest_fitness
            #     if recent_improvement < 0.01:  
            #         print(f"\nConverged after {iteration + 1} iterations!")
            #         break
        
        return self.get_results()
    
    def get_results(self):
        gm1, gm2, L_1, L_2, ID = self.gbest_position
        
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
            'convergence_history': self.gbest_history
        }
        
        return results
    
    def plot_convergence(self):
        plt.figure(figsize=(12, 5))
        
        # Plot 1: Global best convergence
        plt.subplot(1, 2, 1)
        plt.plot(self.gbest_history, 'b-', linewidth=2)
        plt.xlabel('Iteration')
        plt.ylabel('Global Best Area (μm²)')
        plt.title('PSO Convergence - Global Best')
        plt.grid(True, alpha=0.3)
        
        # Plot 2: Swarm diversity
        plt.subplot(1, 2, 2)
        fitness_array = np.array(self.fitness_history)
        avg_fitness = np.mean(fitness_array, axis=1)
        std_fitness = np.std(fitness_array, axis=1)
        
        iterations = range(len(avg_fitness))
        plt.plot(iterations, avg_fitness, 'g-', linewidth=2, label='Average')
        plt.fill_between(iterations, 
                        avg_fitness - std_fitness, 
                        avg_fitness + std_fitness, 
                        alpha=0.3, color='g', label='Std Dev')
        plt.plot(self.gbest_history, 'r--', linewidth=2, label='Global Best')
        plt.xlabel('Iteration')
        plt.ylabel('Area (μm²)')
        plt.title('PSO Convergence - Swarm Statistics')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('pso_convergence.png', dpi=300, bbox_inches='tight')

def main():
    
    # Define initial bounds based on specifications
    gm_ID_range = (3, 20)  # S/A
    L_1_range = (0.15, 3)  # μm
    L_2_range = (0.15, 3)  # μm
    
    # Get feasible region
    gm1_min, gm1_max, gm2_min, gm2_max, L_1_min, L_1_max, L_2_min, L_2_max, ID_min, ID_max = \
        get_feasRegion(gm_ID_range, L_1_range, L_2_range, SR_spec, CL, Power_spec, GBW_spec)
    
    bounds = [
        (gm1_min, gm1_max),
        (gm2_min, gm2_max),
        (L_1_min, L_1_max),
        (L_2_min, L_2_max),
        (ID_min, ID_max)
    ]
    
    print("\nInitial Feasible Bounds:")
    print(f"  gm1: [{gm1_min*1e6:.2f}, {gm1_max*1e6:.2f}] μS")
    print(f"  gm2: [{gm2_min*1e6:.2f}, {gm2_max*1e6:.2f}] μS")
    print(f"  L_1: [{L_1_min:.2f}, {L_1_max:.2f}] μm")
    print(f"  L_2: [{L_2_min:.2f}, {L_2_max:.2f}] μm")
    print(f"  ID:  [{ID_min*1e6:.2f}, {ID_max*1e6:.2f}] μA")
    print()
    
    start_time = time.time()
    
    pso = HybridPSO(
        bounds=bounds,
        n_particles=20,
        max_iterations=300,
        w_max=0.8,
        w_min=0.5,
        c1=1.7,
        c2=1.7,
        max_velocity_updates=5
    )
    
    results = pso.optimize()
    
    end_time = time.time()
    
    if results:
        print("\nOptimal Design Parameters: ")
        print(f"  gm1 = {results['optimal_particle']['gm1']*1e6:.2f} μS")
        print(f"  gm2 = {results['optimal_particle']['gm2']*1e6:.2f} μS")
        print(f"  L_1 = {results['optimal_particle']['L_1']:.2f} μm")
        print(f"  L_2 = {results['optimal_particle']['L_2']:.2f} μm")
        print(f"  ID  = {results['optimal_particle']['ID']*1e6:.2f} μA")
        print(f"  gm/ID_1 = {results['optimal_particle']['gm_ID_1']:.2f} S/A")
        print(f"  gm/ID_2 = {results['optimal_particle']['gm_ID_2']:.2f} S/A")
        
        print("\nOptimal Transistor Sizing:")
        print(f"  W_1 = {results['optimal_sizing']['W_1']:.2f} μm")
        print(f"  W_2 = {results['optimal_sizing']['W_2']:.2f} μm")
        print(f"  L_1 = {results['optimal_sizing']['L_1']:.2f} μm")
        print(f"  L_2 = {results['optimal_sizing']['L_2']:.2f} μm")
        
        print(f"\nOptimal Area: {results['optimal_area']:.2f} μm²")
        
        print("\nPerformance Specifications:")
        specs = results['specifications']
        print(f"  Slew Rate: {specs['SR']*1e-6:.2f} V/μs (spec: {SR_spec*1e-6:.2f})")
        print(f"  GBW: {specs['GBW']*1e-6:.2f} MHz (spec: {GBW_spec*1e-6:.2f})")
        print(f"  Gain: {specs['Gain_dB']:.2f} dB (spec: {Gain_spec_dB:.2f})")
        print(f"  Phase Margin: {specs['PM']:.2f}° (spec: {PM_spec:.2f})")
        print(f"  Power: {specs['Power']*1e6:.2f} μW (spec: {Power_spec*1e6:.2f})")
        
        print(f"\nOptimization Time: {end_time - start_time:.2f} seconds")

        pso.plot_convergence()
        
        save_results_to_file(results)
        
    else:
        print("Optimization failed!")
    
    return results

def save_results_to_file(results):

    with open('pso_optimization_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("5T-OTA AREA OPTIMIZATION USING HYBRID PSO\n")
        f.write("="*60 + "\n\n")
        
        f.write("DESIGN SPECIFICATIONS:\n")
        f.write(f"  VDD = {VDD} V\n")
        f.write(f"  CL = {CL*1e12:.2f} pF\n")
        f.write(f"  Slew Rate ≥ {SR_spec*1e-6:.2f} V/μs\n")
        f.write(f"  GBW ≥ {GBW_spec*1e-6:.2f} MHz\n")
        f.write(f"  Gain ≥ {Gain_spec_dB:.2f} dB\n")
        f.write(f"  Phase Margin ≥ {PM_spec:.2f}°\n")
        f.write(f"  Power ≤ {Power_spec*1e6:.2f} μW\n\n")
        
        f.write("OPTIMAL DESIGN PARAMETERS:\n")
        f.write(f"  gm1 = {results['optimal_particle']['gm1']*1e6:.4f} μS\n")
        f.write(f"  gm2 = {results['optimal_particle']['gm2']*1e6:.4f} μS\n")
        f.write(f"  L_1 = {results['optimal_particle']['L_1']:.4f} μm\n")
        f.write(f"  L_2 = {results['optimal_particle']['L_2']:.4f} μm\n")
        f.write(f"  ID  = {results['optimal_particle']['ID']*1e6:.4f} μA\n")
        f.write(f"  gm/ID_1 = {results['optimal_particle']['gm_ID_1']:.4f} S/A\n")
        f.write(f"  gm/ID_2 = {results['optimal_particle']['gm_ID_2']:.4f} S/A\n\n")
        
        f.write("OPTIMAL TRANSISTOR SIZING:\n")
        f.write(f"  W_1 = {results['optimal_sizing']['W_1']:.4f} μm\n")
        f.write(f"  W_2 = {results['optimal_sizing']['W_2']:.4f} μm\n")
        f.write(f"  L_1 = {results['optimal_sizing']['L_1']:.4f} μm\n")
        f.write(f"  L_2 = {results['optimal_sizing']['L_2']:.4f} μm\n\n")
        
        f.write(f"OPTIMAL AREA: {results['optimal_area']:.4f} μm²\n\n")
        
        f.write("ACHIEVED SPECIFICATIONS:\n")
        specs = results['specifications']
        f.write(f"  Slew Rate = {specs['SR']*1e-6:.4f} V/μs\n")
        f.write(f"  GBW = {specs['GBW']*1e-6:.4f} MHz\n")
        f.write(f"  Gain = {specs['Gain_dB']:.4f} dB\n")
        f.write(f"  Phase Margin = {specs['PM']:.4f}°\n")
        f.write(f"  Power = {specs['Power']*1e6:.4f} μW\n")
    
    print("\nResults saved to outputs/pso_optimization_results.txt")

if __name__ == "__main__":
    results = main()