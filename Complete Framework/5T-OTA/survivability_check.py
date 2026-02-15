import numpy as np

from gmID_sizing import get_specVars
from specs import *

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
        W_1 >= 0.42 and W_2 >= 0.42 and
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