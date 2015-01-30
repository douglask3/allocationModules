#!/usr/bin/env python

""" 
EucFACE Ambient/Elevated CO2 simulations.

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

def main(experiment_id, site, treatment, exp, alloc_model = fixed ):
    
    # dir names
    base_dir = os.path.dirname(os.getcwd())
    param_dir = os.path.join(base_dir, "params")
    met_dir = os.path.join(base_dir, "met_data")
    run_dir = os.path.join(base_dir, "outputs")
    
    shutil.copy(os.path.join(param_dir, "%s_%s_model_indust.cfg" % (experiment_id, site)),
                os.path.join(param_dir, "%s_%s_model_indust_adj_%s.cfg" % (experiment_id, site, exp)))

    itag = "%s_%s_%s_model_indust_adj_%s" % (experiment_id, site, alloc_model, exp)
    otag = "%s_%s_%s_simulation_%s" % (experiment_id, site, alloc_model, exp)
    mtag = "%s_met_data_%s_%s_co2.csv" % (site, treatment, exp)
    out_fn = "D1GDAY%s%s%s%s.csv" % (site, alloc_model, treatment.upper(), exp.upper())
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
                     
                     # control
                     "print_options": "daily",
                 
                    }
    ad.adjust_param_file(cfg_fname, replace_dict)
    G = model.Gday(cfg_fname)
    G.run_sim()

    # translate output to NCEAS style output

    # add this directory to python search path so we can find the scripts!
    sys.path.append(os.path.join(base_dir, "scripts"))
    import translate_GDAY_output_to_EUCFACE_format as tr
    tr.translate_output(out_fname, met_fname)
        
    
if __name__ == "__main__":
    
    
    experiment_id = "FACE"
    site = "EUC"
    alloc_models  = ["FIXED", "ALLOMETRIC", "MAXIMIZEGPP"]
    
    for alloc_model in alloc_models:
        # Ambient
        main(experiment_id, site, treatment="amb", exp="avg", alloc_model=alloc_model)
        main(experiment_id, site, treatment="amb", exp="var", alloc_model=alloc_model)
    
        # Elevated
        main(experiment_id, site, treatment="ele", exp="avg", alloc_model=alloc_model)
        main(experiment_id, site, treatment="ele", exp="var", alloc_model=alloc_model)
    
    
    
    
    
    
    
    
    
    
    