#!/usr/bin/env python

""" EucFACE CO2 simulation.

Spinup assuming a steady state forest.

-> Spinup with forest params, fixed NDEP, fixed CO2
-> Vary NDEP/CO2 for about 200 odd yrs...using forest params so that we get
   through the industrial to the 1980s period.


"""

import os
import shutil
import sys
import subprocess
from gday import gday as model
from gday import adjust_gday_param_file as ad
from gday._version import __version__ as git_revision

__author__  = "Martin De Kauwe"
__version__ = "1.0 (14.12.2014)"
__email__   = "mdekauwe@gmail.com"

def main(experiment_id, site, SPIN_UP=True, POST_INDUST=True, alloc_model = "FIXED"):
    
    # dir names
    base_param_name = "base_start"
    base_dir = os.path.dirname(os.getcwd())
    base_param_dir = "/Users/mq42056055/Documents/gdayFresh/example/params"
    param_dir = os.path.join(base_dir, "params")
    met_dir = os.path.join(base_dir, "met_data")
    run_dir = os.path.join(base_dir, "outputs")

    if SPIN_UP == True:
        
        # copy base files to make two new experiment files
        shutil.copy(os.path.join(base_param_dir, base_param_name + ".cfg"),                
                    os.path.join(param_dir, "%s_%s_model_spinup.cfg" % \
                                                (experiment_id, site)))
        
        # Run model to equilibrium assuming forest, growing C pools from effectively
        # zero
        itag = "%s_%s_model_spinup"    % (experiment_id, site)
        otag = "%s_%s_%s_model_spunup" % (experiment_id, site, alloc_model)
        mtag = "%s_met_data_equilibrium_50_yrs.csv" % (site)
        out_fn = itag + alloc_model + "_equilib.out"
        
        out_param_fname = os.path.join(param_dir, otag + ".cfg")
        cfg_fname = os.path.join(param_dir, itag + ".cfg")
        met_fname = os.path.join(met_dir, mtag)
        out_fname = os.path.join(run_dir, out_fn)
        
        replace_dict = {
                        # git stuff
                        "git_hash": str(git_revision),
                        
                        # files
                        "out_param_fname": "%s" % (out_param_fname),
                        "cfg_fname": "%s" % (cfg_fname),
                        "met_fname": "%s" % (met_fname),
                        "out_fname": "%s" % (out_fname),
                        
                        # default C:N 25.
                        # Canopy height = 22 m average of 6 plots at UWS, site_description_stuff/EucFACE_Plot_Summary.doc
                        "activesoil": "0.001",
                        "activesoiln": "0.00004",
                        "age": "0.0",
                        "branch": "0.001",
                        "branchn": "0.00004",
                        "cstore": "0.0",
                        "nstore": "0.0",
                        "inorgn": "0.00004",
                        "metabsoil": "0.0",
                        "metabsoiln": "0.0",
                        "metabsurf": "0.0",
                        "metabsurfn": "0.0",
                        "passivesoil": "0.001",
                        "passivesoiln": "0.0004",
                        "prev_sma": "1.0",
                        "root": "0.001",
                        "croot": "0.001",
                        "crootn": "0.00004",
                        "rootn": "0.00004",
                        "sapwood": "0.001",
                        "shoot": "0.001",
                        "shootn": "0.00004",
                        "slowsoil": "0.001",
                        "slowsoiln": "0.00004",
                        "stem": "0.001",
                        "stemn": "0.00004",
                        "stemnimm": "0.00004",
                        "stemnmob": "0.0",
                        "structsoil": "0.001",
                        "structsoiln": "0.00004",
                        "structsurf": "0.001",
                        "structsurfn": "0.00004",
                        
                        # parameters
                        "alpha_j": "0.308",  # Taking the theoretical maximum (from Belinda) 0.385 x 0.8 (leaf absorptance) = 0.308
                        "intercep_frac": "0.15",
                        "max_intercep_lai": "3.0",
                        "latitude": "-33.61",
                        "albedo": "0.2",    
                        "finesoil": "0.2",   # silt + clay fraction. Surface soil texture (upper 45 cm) for Clarenden sand: 80 +/- 8% sand, 9 +/- 5% silt, 11 +/- 3% clay
                        "slamax": "4.37",    # 43.7 +/- 1.5 cm2 g 1 dry mass
                        "sla": "4.37",   # 43.7 +/-  1.5 cm2 g 1 dry mass
                        "slazero": "4.37",   # 43.7+/-  1.5 cm2 g 1 dry mass
                        "lai_closed": "0.5",  # I am effectively turning this feature off by setting it so low
                        "c_alloc_fmax": "0.35",
                        "c_alloc_fmin": "0.15",
                        "c_alloc_rmax": "0.35",
                        "c_alloc_rmin": "0.05",
                        "c_alloc_bmax": "0.1", 
                        "c_alloc_bmin": "0.1", 
                        "c_alloc_cmax": "0.0", # turn off coarse roots!
                        "fretrans": "0.5",
                        "rretrans": "0.0",
                        "bretrans": "0.0",
                        "wretrans": "0.0",
                        "cretrans": "0.0",
                        "ncwnewz": "0.003",          #New stem ring N:C at zero leaf N:C (mobile)
                        "ncwnew": "0.003",           #New stem ring N:C at critical leaf N:C (mob)
                        "ncwimmz": "0.003",          #Immobile stem N C at zero leaf N C
                        "ncwimm": "0.003",           #Immobile stem N C at critical leaf N C
                        "ncbnewz": "0.003",          #new branch N C at zero leaf N C
                        "ncbnew": "0.003",           #new branch N C at critical leaf N C
                        "nccnewz": "0.003",          #new coarse root N C at zero leaf N C
                        "nccnew": "0.003",           #new coarse root N C at critical leaf N C
                        "ncrfac": "0.8",
                        "ncmaxfyoung": "0.04",
                        "ncmaxfold": "0.04",
                        "ncmaxr": "0.03",
                        "retransmob": "0.0",
                        "fdecay": "0.6",   # 18 mth turnover * 1/30
                        "fdecaydry": "0.6", # 18 mth turnover * 1/30
                        "rdecay": "0.6",
                        "rdecaydry": "0.6",
                        "crdecay": "0.00",  # turn off coarse roots!
                        "bdecay": "0.02",  # no idea, assuming 50 years
                        "wdecay": "0.02",  # no idea, assuming 50 years
                        "watdecaydry": "0.0",
                        "watdecaywet": "0.1",
                        "ligshoot": "0.18", # Based on white et al. 2000 #"0.145",   # assuming leaf and root same as DE word document
                        "ligroot": "0.22",  # Based on white et al. 2000    # assuming leaf and root same as DE word document
                        "rateuptake": "4.0",
                        "rateloss": "0.1",  # was 0.1
                        "topsoil_depth": "450.0",    # Not needed as I have supplied the root zone water and topsoil water available
                        "rooting_depth": "2000.0",   # Not needed as I have supplied the root zone water and topsoil water available
                        "wcapac_root": "300.0",      # [mm] (FC-WP)*rooting_depth. But using 2.0 m, site_description_stuff/EucFACE_Plot_Summary.doc
                        "wcapac_topsoil": "67.5",    # [mm] (FC-WP)*rooting_depth. But using 0.45 m, site_description_stuff/EucFACE_Plot_Summary.doc
                        "ctheta_topsoil": "0.65",     # Derive based on soil type loamy_sand
                        "ntheta_topsoil": "8.0",     # Derive based on soil type loamy_sand
                        "ctheta_root": "0.525",      # Derive based on soil type sandy_clay_loam
                        "ntheta_root": "5.5",        # Derive based on soil type sandy_clay_loam
                        "topsoil_type": "loamy_sand",
                        "rootsoil_type": "sandy_clay_loam",
                        #"dz0v_dh": "0.1",          
                        #"z0h_z0m": "1.0",
                        #"displace_ratio": "0.67",
                        
                        "dz0v_dh": "0.05",         # Using Value from JULES for TREE PFTs as I don't know what is best. However I have used value from Jarvis, quoted in Jones 1992, pg. 67. Produces a value within the bounds of 3.5-1.1 mol m-2 s-1 Drake, 2010, GCB for canht=17
                        "displace_ratio": "0.75",  # From Jones, pg 67, following Jarvis et al. 1976  
                        "z0h_z0m": "1.0",  
                        
                        "g1": "3.8667",     # Fit by Me to Teresa's data 7th Nov 2013
                        "jmaxna": "31.5",   # "jmaxna": "133.35",  # at 22 deg c
                        "jmaxnb": "0.0",      # "jmaxnb": "0.0",     # at 22 deg c
                        "vcmaxna": "15.6",   # "vcmaxna": "66.04",  # at 22 deg c
                        "vcmaxnb": "0.0",     # "vcmaxnb": "0.0",    # at 22 deg c
                        "measurement_temp": "22.0", # parameters obtained at 22 not 25 degrees
                        "heighto": "4.826",  
                        "htpower": "0.35",   
                        "height0": "5.0",    
                        "height1": "25.0",   
                        "leafsap0": "4000.0", #"4000.0",
                        "leafsap1": "2700.0", #2700
                        "branch0": "5.61",   
                        "branch1": "0.346",
                        "croot0": "0.34",   
                        "croot1": "0.84",  
                        "targ_sens": "0.5",  
                        "density": "480.0",    
                        "nf_min": "0.005",   
                        "nf_crit": "0.015",   
                        "sapturnover": "0.1",
                        
                        # control
                        "alloc_model": alloc_model,
                        "assim_model": "mate",
                        "calc_sw_params": "true",   #false=use fwp values, true=derive them
                        "deciduous_model": "false",  
                        "disturbance": "0",
                        "fixed_stem_nc": "true",
                        "fixleafnc": "false",
                        "grazing": "false",
                        "model_optroot": "false",
                        "modeljm": "1",
                        "ncycle": "true",
                        "nuptake_model": "2",
                        "output_ascii": "true",
                        "passiveconst": "false",
                        "print_options": "end",
                        "ps_pathway": "c3",
                        "respiration_model": "fixed",
                        "strfloat": "0",
                        "trans_model": "1",
                        "use_eff_nc": "0",
                        "use_leuning": "0",
                        "water_stress": "true",
                        "sw_stress_model": "1",  # Sands and Landsberg
                         
        }
        
        ad.adjust_param_file(cfg_fname, replace_dict)
        G = model.Gday(cfg_fname, spin_up=True)
        G.spin_up_pools()

    if POST_INDUST == True:

        # run for 260 odd years post industrial with increasing co2/ndep

        # copy spunup base files to make two new experiment files
        
        
        shutil.copy(os.path.join(param_dir, "%s_%s_model_spunup.cfg" % (experiment_id, site)),
                    os.path.join(param_dir, "%s_%s_model_spunup_adj.cfg" % (experiment_id, site)))

        itag = "%s_%s_model_spunup_adj" % (experiment_id, site)
        otag = "%s_%s_model_indust" % (experiment_id, site)
        mtag = "%s_met_data_industrial_to_present_1750_2011.csv" % (site)
        out_fn = itag + "_indust.out"
        out_param_fname = os.path.join(param_dir, otag + ".cfg")
        cfg_fname = os.path.join(param_dir, itag + ".cfg")
        met_fname = os.path.join(met_dir, mtag)
        out_fname = os.path.join(run_dir, out_fn)

        replace_dict = {
                         # git stuff
                        "git_hash": str(git_revision),
                        
                         # files
                         "out_param_fname": "%s" % (out_param_fname),
                         "cfg_fname": "%s" % (cfg_fname),
                         "met_fname": "%s" % (met_fname),
                         "out_fname": "%s" % (out_fname),
                        
                         
                        }
        ad.adjust_param_file(cfg_fname, replace_dict)
        G = model.Gday(cfg_fname)
        G.run_sim()

if __name__ == "__main__":

    experiment_id = "FACE"
    site          = "EUC"
    alloc_models  = ["FIXED", "ALLOMETRIC", "MAXIMIZEGPP"]
    for alloc_model in alloc_models:
        main(experiment_id, site, SPIN_UP=True, POST_INDUST=True, alloc_model = alloc_model)
    
    
    