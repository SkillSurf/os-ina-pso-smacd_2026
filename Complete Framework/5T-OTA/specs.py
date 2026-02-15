import numpy as np

# 5T OTA design parameters
VDD = 1.8
CL  = 2e-12

# 5T OTA design specifications
SR_spec = 1e6
GBW_spec = 1e6
Gain_spec_dB = 38
Gain_spec = 10**(Gain_spec_dB/20)
PM_spec = 65
Power_spec = 10e-6

# Mixed Variable Hybrid-PSO parameters
N_PARTICLES = 5
MAX_ITERATIONS = 2
MAX_VELOCITY_UPDATES = 3

# Range of sizing variables
gm_ID_range = (3, 20)
L_DISCRETE_VALUES = np.array([0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 
                               0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 
                               0.90, 1.00, 2.00, 3.00])