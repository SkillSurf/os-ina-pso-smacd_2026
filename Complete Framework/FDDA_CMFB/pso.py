import numpy as np
from survivability_check import L_DISCRETE_VALUES, survivability_test

class PSO:
    def __init__(self, cont_bounds, n_L_values, n_particles, 
                 w=0.7, c1=1.7, c2=1.7, max_velocity_updates=5):

        self.cont_bounds = cont_bounds
        self.n_L_values = n_L_values
        self.n_particles = n_particles
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.max_velocity_updates = max_velocity_updates
        
        self.continuous_indices = [0, 1, 2, 3, 4, 5, 13]
        self.discrete_indices = [6, 7, 8, 9, 10, 11, 12]
        self.n_cont = len(self.continuous_indices)
        self.n_disc = len(self.discrete_indices)
        
        self.velocities = np.zeros((n_particles, self.n_cont))
        
        self.pbest_positions = None
        self.pbest_fitness = None
        
        self.gbest_position = None
        self.gbest_fitness = np.inf
        self.gbest_specs = None
        
        self.discrete_probs = np.ones((self.n_disc, n_L_values)) / n_L_values
        
    def initialize_velocities(self):
        for i, cont_idx in enumerate(self.continuous_indices):
            bound_range = self.cont_bounds[i][1] - self.cont_bounds[i][0]

            self.velocities[:, i] = np.random.uniform(
                -0.1 * bound_range,
                0.1 * bound_range,
                self.n_particles
            )
    
    def set_initial_best(self, particles, fitness, specs_list):
        self.pbest_positions = particles.copy()
        self.pbest_fitness = fitness.copy()
        
        best_idx = np.argmin(fitness)
        self.gbest_position = particles[best_idx].copy()
        self.gbest_fitness = fitness[best_idx]
        self.gbest_specs = specs_list[best_idx]
    
    def update_discrete_probabilities(self):
        sorted_indices = np.argsort(self.pbest_fitness)
        superior_half = sorted_indices[:self.n_particles//2]
        
        for var_idx in range(self.n_disc):
            disc_idx = self.discrete_indices[var_idx]
            
            counts = np.zeros(self.n_L_values)
            for sup_idx in superior_half:
                value_idx = int(self.pbest_positions[sup_idx, disc_idx])
                counts[value_idx] += 1
            
            alpha = 0.7
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
    
    def continuous_update(self, particle_idx, current_position):
        new_cont_vars = np.zeros(self.n_cont)
        
        for i, cont_idx in enumerate(self.continuous_indices):
            r1 = np.random.random()
            r2 = np.random.random()
            
            current_pos = current_position[cont_idx]
            pbest_pos = self.pbest_positions[particle_idx, cont_idx]
            gbest_pos = self.gbest_position[cont_idx]
            
            cognitive = self.c1 * r1 * (pbest_pos - current_pos)
            social = self.c2 * r2 * (gbest_pos - current_pos)
            
            self.velocities[particle_idx, i] = (
                self.w * self.velocities[particle_idx, i] + cognitive + social
            )
            
            new_cont_vars[i] = current_pos + self.velocities[particle_idx, i]
            
            new_cont_vars[i] = np.clip(
                new_cont_vars[i],
                self.cont_bounds[i][0],
                self.cont_bounds[i][1]
            )
        
        return new_cont_vars
    
    def discrete_update(self):

        new_disc_vars = np.zeros(self.n_disc)
        
        for var_idx in range(self.n_disc):
            probs = self.discrete_probs[var_idx, :]
            new_disc_vars[var_idx] = np.random.choice(self.n_L_values, p=probs)
        
        return new_disc_vars
    
    def generate_offspring(self, particle_idx, current_position):

        new_cont_vars = self.continuous_update(particle_idx, current_position)
        
        new_disc_vars = self.discrete_update()
        
        offspring = np.zeros(self.n_cont + self.n_disc)
        offspring[self.continuous_indices] = new_cont_vars
        offspring[self.discrete_indices] = new_disc_vars
        
        passed, area, specs = survivability_test(offspring)
            
        return offspring, area, specs, True

    def update_swarm(self, particles, fitness):
        
        new_particles = particles.copy()
        new_fitness = fitness.copy()
        need_simulator_check = []
        
        self.update_discrete_probabilities()
        
        for i in range(self.n_particles):
            offspring, area, specs, from_reproduction = self.generate_offspring(i, particles[i])
            
            new_particles[i] = offspring
            new_fitness[i] = area
            need_simulator_check.append(i)
        
        return new_particles, new_fitness, need_simulator_check
    
    def get_best_solution(self):
        gm_ID_1, gm_ID_2, gm_ID_3, gm_ID_4, gm_ID_5, gm_ID_6 = self.gbest_position[0:6]
        L_1_idx, L_2_idx, L_3_idx, L_4_idx, L_5_idx, L_6_idx, L_7_idx = self.gbest_position[6:13]
        I_T = self.gbest_position[13]
        
        L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
        L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
        L_3 = L_DISCRETE_VALUES[int(L_3_idx)]
        L_4 = L_DISCRETE_VALUES[int(L_4_idx)]
        L_5 = L_DISCRETE_VALUES[int(L_5_idx)]
        L_6 = L_DISCRETE_VALUES[int(L_6_idx)]
        L_7 = L_DISCRETE_VALUES[int(L_7_idx)]
        
        return {
            'gm_ID_1': gm_ID_1,
            'gm_ID_2': gm_ID_2,
            'gm_ID_3': gm_ID_3,
            'gm_ID_4': gm_ID_4,
            'gm_ID_5': gm_ID_5,
            'gm_ID_6': gm_ID_6,
            'L_1': L_1,
            'L_2': L_2,
            'L_3': L_3,
            'L_4': L_4,
            'L_5': L_5,
            'L_6': L_6,
            'L_7': L_7,
            'I_T': I_T,
            'area': self.gbest_fitness,
            'specs': self.gbest_specs
        }