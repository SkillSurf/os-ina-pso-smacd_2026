import numpy as np

from gmID_sizing import get_Area, get_specVars
from specs import *

# ==========================================================================
# Function to test if a particle meets all design specifications (EQUATIONS)
# ==========================================================================
def survivability_test(particle, verbose=False):
    """
    Test if a particle meets all design specifications
    particle = [gm_ID_1, ..., gm_ID_6, L_1_idx, ..., L_6_idx, I_T]
    """
    gm_ID_1 = particle[0]
    gm_ID_2 = particle[1]
    gm_ID_3 = particle[2]
    gm_ID_4 = particle[3]
    gm_ID_5 = particle[4]
    gm_ID_6 = particle[5]

    L_1_idx = particle[6]
    L_2_idx = particle[7]
    L_3_idx = particle[8]
    L_4_idx = particle[9]
    L_5_idx = particle[10]
    L_6_idx = particle[11]

    I_T = particle[12]

    L_1 = L_DISCRETE_VALUES[int(L_1_idx)]
    L_2 = L_DISCRETE_VALUES[int(L_2_idx)]
    L_3 = L_DISCRETE_VALUES[int(L_3_idx)]
    L_4 = L_DISCRETE_VALUES[int(L_4_idx)]
    L_5 = L_DISCRETE_VALUES[int(L_5_idx)]
    L_6 = L_DISCRETE_VALUES[int(L_6_idx)]

    gm_ID = {'gm_ID_1': gm_ID_1, 'gm_ID_2': gm_ID_2, 'gm_ID_3': gm_ID_3, 
             'gm_ID_4': gm_ID_4, 'gm_ID_5': gm_ID_5, 'gm_ID_6': gm_ID_6}

    L = {'L_1': L_1, 'L_2': L_2, 'L_3': L_3, 'L_4': L_4, 'L_5': L_5, 'L_6': L_6}

    W, L, gm, gds, C, Vgs, gamma, flicker, ID = get_specVars(gm_ID, L, V_A, V_B, I_T)
    
    if W is None or any(w is None for w in W.values()):
        return False, np.inf, None

    # ===================
    # DC Gain Calculation
    # ===================
    Gm_dm = gm['gm_1']
    Rout_A = (1 / gds['gds_3']) + (1 / gds['gds_2']) + (gm['gm_3'] * (1 / gds['gds_3']) * (1 / gds['gds_2']))
    Rparr_dm = 1 / (gds['gds_5'] + (2 * gds['gds_1']))
    Rout_B_dm = (1 / gds['gds_4']) + Rparr_dm + (gm['gm_4'] * (1 / gds['gds_4']) * Rparr_dm)
    Rout_dm = (Rout_A * Rout_B_dm) / (Rout_A + Rout_B_dm)
    Gain_dc_calc = Gm_dm * Rout_dm
    
    # ==================================
    # Gain-Bandwidth Product Calculation
    # ==================================
    C_load = (2 * CL) + C['Cdd_3'] + C['Cdd_4'] + C['Cgg_7']
    GBW_rads = Gm_dm / C_load
    GBW_calc = GBW_rads / (2 * np.pi)
    
    # ========================
    # Phase Margin Calculation
    # ========================
    Rfold = 1 / (gm['gm_4'] + gds['gds_5'] + (2 * gds['gds_1']))
    Cfold = C['Css_4'] + C['Cdd_5'] + (2 * C['Cdd_1'])

    non_dom_pole = 1 / (Rfold * Cfold)
    PM_calc = 90 - (np.arctan(GBW_rads / non_dom_pole) * (180 / np.pi))
    
    # =====================
    # Slew Rate Calculation
    # =====================
    SR_calc = 2 * ID['ID_6'] / C_load
    
    # =================
    # Power Calculation
    # =================
    Power_calc = 4 * ID['ID_5'] * VDD
    
    # # ================================
    # # Input Referred Noise Calculation
    # # ================================
    # noise_1 = 4 * (((4 * k * temp * gamma['gamma_1']) / gm['gm_1']) + (flicker['flicker_1'] / gm['gm_1'] / freq))
    # noise_5 = 2 * (((4 * k * temp * gamma['gamma_5'] * gm['gm_5']) / (gm['gm_1'] ** 2)) + ((flicker['flicker_5'] / freq) * (gm['gm_5'] / (gm['gm_1'] ** 2))))
    # noise_2 = 2 * (((4 * k * temp * gamma['gamma_2'] * gm['gm_2']) / (gm['gm_1'] ** 2)) + ((flicker['flicker_2'] / freq) * (gm['gm_2'] / (gm['gm_1'] ** 2))))
    # noise_calc = np.sqrt(noise_1 + noise_5 + noise_2)
    
    # # ================
    # # CMRR Calculation
    # # ================
    # C_tail = C['Cdd_6'] + (2 * C['Css_1'])
    # Z_tail = np.abs(1 / (gds['gds_6'] + (1j * 2 * np.pi * freq * C_tail)))
    # Gm_cm = 1 / Z_tail

    # Rparr_cm = 1 / (gds['gds_5'] + (1 / ((0.5 / gds['gds_1']) + ((1 / gds['gds_6']) * (1 + (gm['gm_1'] / gds['gds_1']))))))
    # Rout_B_cm = (1 / gds['gds_4']) + ((1 + (gm['gm_4'] / gds['gds_4'])) * Rparr_cm)
    # Rout_cm = (Rout_A * Rout_B_cm) / (Rout_A + Rout_B_cm)
    # Zout_cm = abs(1 / ((1 / Rout_cm) + (1j * 2 * np.pi * freq * C_load)))
    # Gain_cm_open = Gm_cm * Zout_cm

    # Lgain_cmfb = abs((gm['gm_2'] * gm['gm_7']) / ((1j * 2 * np.pi * freq * C_load) * gm['gm_8']))
    # Gain_cm_calc = Gain_cm_open / (1 + Lgain_cmfb)

    # Zout_dm = abs(1 / ((1 / Rout_dm) + (1j * 2 * np.pi * freq * C_load)))
    # Gain_dm_calc = Gm_dm * Zout_dm

    # CMRR_calc = Gain_dm_calc / Gain_cm_calc

    # ================
    # Area Calculation
    # ================
    Area_active = get_Area(W, L)
    
    # ========================
    # Bias Voltage Calculation
    # ========================
    V_B1 = VDD - Vgs['Vgs_6']
    V_B2 = Vgs['Vgs_5']
    V_B3 = V_B + Vgs['Vgs_4']
    V_B4 = V_A - Vgs['Vgs_3']
    V_CMFB = VDD - Vgs['Vgs_2']
    
    specs_met = (
        Gain_dc_calc >= Gain_dc_spec and
        GBW_calc >= GBW_spec and
        PM_calc >= PM_spec and
        SR_calc >= SR_spec and
        Power_calc <= Power_spec and
        # noise_calc <= noise_spec and
        # CMRR_calc >= CMRR_spec and
        W['W_1'] >= 0.42 and W['W_2'] >= 0.42 and
        W['W_3'] >= 0.42 and W['W_4'] >= 0.42 and
        W['W_5'] >= 0.42 and W['W_6'] >= 0.42 and
        W['W_7'] >= 0.42 and W['W_8'] >= 0.42 and
        V_B1 > 0 and V_B1 < VDD and
        V_B2 > 0 and V_B2 < VDD and
        V_B3 > 0 and V_B3 < VDD and
        V_B4 > 0 and V_B4 < VDD and
        V_CMFB > 0 and V_CMFB < VDD and
        Area_active > 0
    )
    
    specs_dict = {
        'Gain_dB': 20*np.log10(Gain_dc_calc),
        'GBW': GBW_calc,        
        'PM': PM_calc,
        'SR': SR_calc,
        'Power': Power_calc,
        'V_CMFB': V_CMFB,
        # 'Noise': noise_calc,
        # 'CMRR_dB': 20*np.log10(CMRR_calc),
        'Area': Area_active,
        'W_1': W['W_1'], 'L_1': L['L_1'],
        'W_2': W['W_2'], 'L_2': L['L_2'],
        'W_3': W['W_3'], 'L_3': L['L_3'],
        'W_4': W['W_4'], 'L_4': L['L_4'],
        'W_5': W['W_5'], 'L_5': L['L_5'],
        'W_6': W['W_6'], 'L_6': L['L_6'],
        'W_7': W['W_7'], 'L_7': L['L_7'],
        'W_8': W['W_8'], 'L_8': L['L_8'],
        'V_B1': V_B1,
        'V_B2': V_B2,
        'V_B3': V_B3,
        'V_B4': V_B4
    }
    
    if verbose and specs_met:
        print(f"  Gain: {20*np.log10(Gain_dc_calc):.3f} dB (spec: {Gain_dc_spec_dB:.3f})")
        print(f"  GBW: {GBW_calc*1e-6:.3f} MHz (spec: {GBW_spec*1e-6:.3f})")
        print(f"  PM: {PM_calc:.3f}° (spec: {PM_spec:.3f})")
        print(f"  SR: {SR_calc*1e-6:.3f} V/μs (spec: {SR_spec*1e-6:.3f})")
        print(f"  Power: {Power_calc*1e6:.3f} μW (spec: {Power_spec*1e6:.3f})")
        # print(f"  Noise: {noise_calc*1e6:.3f} μV/√Hz (spec: {noise_spec*1e6:.3f})")
        # print(f"  CMRR: {20*np.log10(CMRR_calc):.3f} dB (spec: {CMRR_spec_dB:.3f})")
        print(f"  Area: {Area_active:.3f} μm²")
    
    return specs_met, Area_active, specs_dict