from pygmid import Lookup as lk

from specs import *

# ==========================================================================
# Function to calculate W for each transistor based on gm_ID, Vds, L, and ID
# ==========================================================================
def get_W(gm_ID, Vds, L, ID):

    # LUT readout for CMFB circuit transistors (M7 and M8)
    Vds['Vds_8'] = PCH.lookupVGS(GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2'])
    Vds['Vds_7'] = VDD - Vds['Vds_8'] - Vds['Vds_5']

    gm_ID['gm_ID_7'] = NCH.lookup('GM_ID', VGS=Vds['Vds_4'], VDS=Vds['Vds_7'], VSB=0, L=L['L_7'])
    gm_ID['gm_ID_8'] = PCH.lookup('GM_ID', VGS=Vds['Vds_8'], VDS=Vds['Vds_8'], VSB=0, L=L['L_8'])

    # Read the current density (A/µm) from the LUTs
    JD_1 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1'])
    JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2'])
    JD_3 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=0, L=L['L_3'])
    JD_4 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=0, L=L['L_4'])
    JD_5 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5'])
    JD_6 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=0, L=L['L_6'])
    JD_7 = NCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_7'], VDS=Vds['Vds_7'], VSB=0, L=L['L_7'])
    JD_8 = PCH.lookup('ID_W', GM_ID=gm_ID['gm_ID_8'], VDS=Vds['Vds_8'], VSB=0, L=L['L_8'])

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

    return W

# ===================================================================================================
# Function to calculate all the required variables for each transistor based on gm_ID, Vds, L, and ID
# ===================================================================================================
def get_specVars(gm_ID, Vds, L, ID):

    W = get_W(gm_ID, Vds, L, ID)

    # Return "None" if any one of W is none
    if any(w is None for w in W.values()):
        return None, None, None, None, None, None, None
    else:

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
            'gds_1': gm['gm_1'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'gds_2': gm['gm_2'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2']),
            'gds_3': gm['gm_3'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=0, L=L['L_3']),
            'gds_4': gm['gm_4'] / NCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=0, L=L['L_4']),
            'gds_5': gm['gm_5'] / NCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5']),
            'gds_6': gm['gm_6'] / PCH.lookup('GM_GDS', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=0, L=L['L_6'])
        }

        # Read the capacitances (F) from the LUTs
        C = {
            'Cdd_1': gm['gm_1'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'Cdd_3': gm['gm_3'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=0, L=L['L_3']),
            'Cdd_4': gm['gm_4'] / NCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=0, L=L['L_4']),
            'Cdd_5': gm['gm_5'] / NCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5']),
            'Cdd_6': gm['gm_6'] / PCH.lookup('GM_CDD', GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=0, L=L['L_6']),

            'Css_1': gm['gm_1'] / PCH.lookup('GM_CSS', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'Css_4': gm['gm_4'] / NCH.lookup('GM_CSS', GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=0, L=L['L_4'])
        }

        # Read the gate-source voltage (V) from the LUTs
        Vgs = {
            'Vgs_1': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'Vgs_2': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2']),
            'Vgs_3': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_3'], VDS=Vds['Vds_3'], VSB=0, L=L['L_3']),
            'Vgs_4': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_4'], VDS=Vds['Vds_4'], VSB=0, L=L['L_4']),
            'Vgs_5': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5']),
            'Vgs_6': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_6'], VDS=Vds['Vds_6'], VSB=0, L=L['L_6']),
            'Vgs_7': NCH.lookupVGS(GM_ID=gm_ID['gm_ID_7'], VDS=Vds['Vds_7'], VSB=0, L=L['L_7']),
            'Vgs_8': PCH.lookupVGS(GM_ID=gm_ID['gm_ID_8'], VDS=Vds['Vds_8'], VSB=0, L=L['L_8'])
        }

        # Read the gamma values from the LUTs
        gamma = {
            'gamma_1': PCH.gamma(GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'gamma_2': PCH.gamma(GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2']),
            'gamma_5': NCH.gamma(GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5'])
        }
        
        # Read the flicker noise (nA/√Hz) from the LUTs
        flicker = {
            'flicker_1': PCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_1'], VDS=Vds['Vds_1'], VSB=0, L=L['L_1']),
            'flicker_2': PCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_2'], VDS=Vds['Vds_2'], VSB=0, L=L['L_2']),
            'flicker_5': NCH.lookup('SFL_GM', GM_ID=gm_ID['gm_ID_5'], VDS=Vds['Vds_5'], VSB=0, L=L['L_5'])
        }

    return W, gm, gds, C, Vgs, gamma, flicker

# ============================================================
# Function to calculate the feasible range of design variables
# ============================================================
def get_feasRegion(gm_ID_range, V_A_range, V_B_range, V_C_range, L_discrete_values):

    # Range of gm/ID values to consider for the design
    gm_ID_min = gm_ID_range[0]
    gm_ID_max = gm_ID_range[1]

    # Minimum current calculations based on slew rate
    I_T_min = SR_spec * CL
    I_X_min = I_T_min * 0.01  # Assuming IX is at least 1% of IT

    # Maximum current calculations based on power budget
    I_T_max = (Power_spec / VDD / 4) - I_X_min
    I_X_max = (Power_spec / VDD / 4) - I_T_min

    L_available = L_discrete_values
    n_L_values = len(L_available)

    V_A_min = V_A_range[0]
    V_A_max = V_A_range[1]

    V_B_min = V_B_range[0]
    V_B_max = V_B_range[1]

    V_C_min = V_C_range[0]
    V_C_max = V_C_range[1]    

    return gm_ID_min, gm_ID_max, L_available, n_L_values, I_T_min, I_T_max, I_X_min, \
        I_X_max, V_A_min, V_A_max, V_B_min, V_B_max, V_C_min, V_C_max

# ================================
# Function to calculate total area
# ================================
def get_A(W, L):

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