import numpy as np
from scipy.interpolate import interp1d
from pygmid import Lookup as lk

from specs import *

# ==============================================================
# NEW LOOK-UP TABLE (LUT) FOR DIODE CONNECTED DEVICES
# ==============================================================
# Function to create diode-connected LUT
def diode_connected_lut(device_data, vgs_sweep):
    L_values = np.round(np.unique(device_data['L']), 2)
    diode_lut = {}

    for l_val in L_values:
        gm_id = device_data.lookup('GM_ID', L=l_val, VGS=vgs_sweep, VDS=vgs_sweep, VSB=0)
        diode_lut[l_val] = np.diag(gm_id)

    return diode_lut

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
# ==============================================================

def get_W(gm1, gm2, L_1, L_2, ID):
    gm_ID_1 = gm1 / ID
    gm_ID_2 = gm2 / ID

    if gm_ID_1 <= gm_ID_range[0] or gm_ID_2 <= gm_ID_range[0] or gm_ID_1 >= gm_ID_range[1] or gm_ID_2 >= gm_ID_range[1]:
        return None, None, None, None, None
    else:
        Vgs_2 = getVGS_diode('PMOS', gm_ID_2, L_2)

        JD_1 = NCH.lookup('ID_W', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
        JD_2 = PCH.lookup('ID_W', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

        W_1 = ID / JD_1
        W_2 = ID / JD_2

    return W_1, W_2, gm_ID_1, gm_ID_2, Vgs_2

def get_specVars(gm1, gm2, L_1, L_2, ID):

    W_1, W_2, gm_ID_1, gm_ID_2, Vgs_2 = get_W(gm1, gm2, L_1, L_2, ID)

    if W_1 is None or W_2 is None:
        return None, None, None, None, None, None
    else:
        Cdd_1 = gm1 / NCH.lookup('GM_CDD', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
        Cdd_2 = gm2 / PCH.lookup('GM_CDD', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
        Cpar = Cdd_1 + Cdd_2

        Cgg_2 = gm2 / PCH.lookup('GM_CGG', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)
        Cx = Cpar + Cgg_2

        gds_1 = gm1 / NCH.lookup('GM_GDS', GM_ID=gm_ID_1, VDS=VDD/2, VSB=0, L=L_1)
        gds_2 = gm2 / PCH.lookup('GM_GDS', GM_ID=gm_ID_2, VDS=Vgs_2, VSB=0, L=L_2)

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

NCH = lk('../../sky130_lookup/simulation/nfet_01v8.mat')
PCH = lk('../../sky130_lookup/simulation/pfet_01v8.mat')

vgs_sweep = np.arange(0.05, VDD+0.1, 0.01)

# Create LUTs for diode-connected NMOS and PMOS
nch_results = diode_connected_lut(NCH, vgs_sweep)
pch_results = diode_connected_lut(PCH, vgs_sweep)