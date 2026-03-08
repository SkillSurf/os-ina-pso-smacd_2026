import sys
import os
from contextlib import contextmanager
from pygmid import Lookup as lk

from specs import *

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

# =========================================================================
# Function to calculate M1 parameters using an iterative convergence method
# =========================================================================
def get_inputParams(gm_ID, L, V_B):

    try:
        # Get the Vgs value based on Bulk voltage
        Vgs = PCH.lookupVGS(GM_ID=gm_ID, VDB=(VDD-V_B), VGB=(VDD-VCM), L=L)

        # Calculate the intermediate node
        V_C = VCM + Vgs
        if V_C < 0 or V_C > VDD:
            return None, None, None, None
        
        # Calculate Vds and Vsb voltages for M1
        Vds = V_C - V_B
        Vsb = VDD - V_C
        if Vds < 0.15 or Vsb <= 0:
            return None, None, None, None

        return Vgs, Vds, Vsb, V_C
    
    except:
        return None, None, None, None

# =========================================================================
# Function to get parameters for each transistor based on gm_ID, L, and I_T
# =========================================================================
def get_params(gm_ID, L, V_A, V_B, I_T):

    with silence_stdout():
        # Get the initial Vgs, Vds, and tail node voltage (V_C) for M1
        Vgs_1, Vds_1, Vsb_1, V_C = get_inputParams(gm_ID['gm_ID_1'], L['L_1'], V_B)
        if Vgs_1 is None or Vds_1 is None or Vsb_1 is None or V_C is None:
            return None, None, None, None, None, None, None
        
        # Calculate Vds for all transistors based on the converged V_C and given node voltages
        Vds = {
            'Vds_1': Vds_1,
            'Vds_2': VDD - V_A,
            'Vds_3': V_A - VCM,
            'Vds_4': VCM - V_B,
            'Vds_5': V_B,
            'Vds_6': VDD - V_C
        }
        if Vds['Vds_2'] < 0.15 or Vds['Vds_3'] < 0.15 or Vds['Vds_4'] <= 0 or Vds['Vds_5'] <= 0 or Vds['Vds_6'] < 0.15:
            return None, None, None, None, None, None, None

        # Calculate Vsb for all transistors
        Vsb = {
            'Vsb_1': Vsb_1,
            'Vsb_2': 0,
            'Vsb_3': VDD - V_A,
            'Vsb_4': V_B,
            'Vsb_5': 0,
            'Vsb_6': 0,
            'Vsb_7': V_B,
            'Vsb_8': 0
        }

        try:
            # LUT readout for CMFB circuit transistors (M7 and M8)
            Vds['Vds_8'] = PCH.lookupVGS(GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=Vsb['Vsb_2'], L=L['L_2'])
            Vds['Vds_7'] = VDD - Vds['Vds_8'] - Vds['Vds_5']
            if Vds['Vds_7'] <= 0 or Vds['Vds_8'] < 0.15:
                return None, None, None, None, None, None, None
            
            # Append gm_ID values for M7 and M8
            gm_ID['gm_ID_7'] = NCH.lookup('GM_ID', VGS=Vds['Vds_4'], VDS=Vds['Vds_7'], VSB=Vsb['Vsb_7'], L=L['L_7'])
            gm_ID['gm_ID_8'] = gm_ID['gm_ID_2']

            # Append L values for M8
            L['L_8'] = L['L_2']

            I_X = I_T / M

            # Create a dictionary to hold the current density (A/µm) for each transistor
            ID = {
                'ID_1': I_T / 2,
                'ID_2': I_X,
                'ID_3': I_X,
                'ID_4': I_X,
                'ID_5': I_T + I_X,
                'ID_6': I_T,
                'ID_7': (I_T + I_X) / 2,
                'ID_8': I_T + I_X
            }
            
            # Read the gate-source voltage (V) from the LUTs
            Vgs = {
                'Vgs_1': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                'Vgs_2': Vds['Vds_8'],
                'Vgs_3': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=Vsb['Vsb_3'], L=L['L_3']),
                'Vgs_4': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=Vsb['Vsb_4'], L=L['L_4']),
                'Vgs_5': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5']),
                'Vgs_6': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=Vsb['Vsb_6'], L=L['L_6']),
                'Vgs_7': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_7'], VDS=Vds['Vds_7'], VSB=Vsb['Vsb_7'], L=L['L_7']),
                'Vgs_8': Vds['Vds_8']
            }
            
            # Read the current density (A/µm) from the LUTs
            JD_1 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1'])
            JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=Vsb['Vsb_2'], L=L['L_2'])
            JD_3 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=Vsb['Vsb_3'], L=L['L_3'])
            JD_4 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=Vsb['Vsb_4'], L=L['L_4'])
            JD_5 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5'])
            JD_6 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=Vsb['Vsb_6'], L=L['L_6'])
            JD_7 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_7'], VDS=Vds['Vds_7'], VSB=Vsb['Vsb_7'], L=L['L_7'])
            JD_8 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_8'], VDS=Vds['Vds_8'], VSB=Vsb['Vsb_8'], L=L['L_8'])

        except:
            return None, None, None, None, None, None, None

    # Calculate W for each transistor
    W = {
        'W_1': ID['ID_1'] / JD_1,
        'W_2': ID['ID_2'] / JD_2,
        'W_3': ID['ID_3'] / JD_3,
        'W_4': ID['ID_4'] / JD_4,
        'W_5': ID['ID_5'] / JD_5,
        'W_6': ID['ID_6'] / JD_6,
        'W_7': ID['ID_7'] / JD_7,
        'W_8': ID['ID_8'] / JD_8
    }

    return W, L, gm_ID, Vds, Vgs, Vsb, ID

# ===============================================================================================
# Function to calculate all the required variables for each transistor based on gm_ID, L, and I_T
# ===============================================================================================
def get_specVars(gm_ID, L, V_A, V_B, I_T):

    W, L, gm_ID, Vds, Vgs, Vsb, ID = get_params(gm_ID, L, V_A, V_B, I_T)

    with silence_stdout():
        # Return "None" if any one of params is none
        if any(arg is None for arg in [W, L, gm_ID, Vds, Vgs, Vsb, ID]):
            return None, None, None, None, None, None, None, None, None
        else:
            try:
                # Calculate transconductance (S) for each transistor
                gm = {
                    'gm_1': gm_ID['gm_ID_1'] * ID['ID_1'],
                    'gm_2': gm_ID['gm_ID_2'] * ID['ID_2'],
                    'gm_3': gm_ID['gm_ID_3'] * ID['ID_3'],
                    'gm_4': gm_ID['gm_ID_4'] * ID['ID_4'],
                    'gm_5': gm_ID['gm_ID_5'] * ID['ID_5'],
                    'gm_6': gm_ID['gm_ID_6'] * ID['ID_6'],
                    'gm_7': gm_ID['gm_ID_7'] * ID['ID_7'],
                    'gm_8': gm_ID['gm_ID_8'] * ID['ID_8']
                }

                # Read the drain conductance (S) from the LUTs
                gds = {
                    'gds_1': gm['gm_1'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                    'gds_2': gm['gm_2'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=Vsb['Vsb_2'], L=L['L_2']),
                    'gds_3': gm['gm_3'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=Vsb['Vsb_3'], L=L['L_3']),
                    'gds_4': gm['gm_4'] / NCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=Vsb['Vsb_4'], L=L['L_4']),
                    'gds_5': gm['gm_5'] / NCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5']),
                    'gds_6': gm['gm_6'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=Vsb['Vsb_6'], L=L['L_6'])
                }

                # Read the capacitances (F) from the LUTs
                C = {
                    'Cdd_1': gm['gm_1'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                    'Cdd_3': gm['gm_3'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=Vsb['Vsb_3'], L=L['L_3']),
                    'Cdd_4': gm['gm_4'] / NCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=Vsb['Vsb_4'], L=L['L_4']),
                    'Cdd_5': gm['gm_5'] / NCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5']),
                    'Cdd_6': gm['gm_6'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=Vsb['Vsb_6'], L=L['L_6']),

                    'Css_1': gm['gm_1'] / PCH.lookup('GM_CSS', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                    'Css_4': gm['gm_4'] / NCH.lookup('GM_CSS', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=Vsb['Vsb_4'], L=L['L_4']),

                    'Cgg_7': gm['gm_7'] / NCH.lookup('GM_CGG', GM_ID=gm_ID['gm_ID_7'], VDS=Vds['Vds_7'], VSB=Vsb['Vsb_7'], L=L['L_7'])
                }

                # Read the gamma values from the LUTs
                gamma = {
                    'gamma_1': PCH.gamma(GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                    'gamma_2': PCH.gamma(GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=Vsb['Vsb_2'], L=L['L_2']),
                    'gamma_5': NCH.gamma(GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5'])
                }
                
                # Read the flicker noise (nA/√Hz) from the LUTs
                flicker = {
                    'flicker_1': PCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=Vsb['Vsb_1'], L=L['L_1']),
                    'flicker_2': PCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=Vsb['Vsb_2'], L=L['L_2']),
                    'flicker_5': NCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=Vsb['Vsb_5'], L=L['L_5'])
                }
                
            except:
                return None, None, None, None, None, None, None, None, None

    return W, L, gm, gds, C, Vgs, gamma, flicker, ID

# ============================================================
# Function to calculate the feasible range of design variables
# ============================================================
def get_feasRegion(L_discrete_values):

    # Minimum current calculations based on slew rate
    I_T_min = SR_spec * (2 * CL)
    # Maximum current calculations based on power budget
    I_T_max = Power_spec / VDD / (4 * (1 + (1 / M)))

    L_available = L_discrete_values
    n_L_values = len(L_available)   

    return L_available, n_L_values, I_T_min, I_T_max

# ================================
# Function to calculate total area
# ================================
def get_Area(W, L):

    # Formula for calculating area based on W and L of each transistor
    area = (4 * W['W_1'] * L['L_1']) \
            + (2 * W['W_2'] * L['L_2']) \
            + (2 * W['W_3'] * L['L_3']) \
            + (2 * W['W_4'] * L['L_4']) \
            + (4 * W['W_5'] * L['L_5']) \
            + (2 * W['W_6'] * L['L_6']) \
            + (4 * W['W_7'] * L['L_7']) \
            + (2 * W['W_8'] * L['L_8'])
    
    return area

NCH = lk('../../sky130_lookup/simulation/nfet_01v8.mat')
PCH = lk('../../sky130_lookup/simulation/pfet_01v8.mat')