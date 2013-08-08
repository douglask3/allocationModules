"""
G'DAY default control flags

Read into the model unless the user changes these at runtime with definitions
in the .INI file

"""

__author__  = "Martin De Kauwe"
__version__ = "1.0 (05.09.2011)"
__email__   = "mdekauwe@gmail.com"

assim_model = "mate"       # bewdy or mate?
nuptake_model = 1          # 0=constant uptake, 1=func of N inorgn, 2=depends on rate of soil N availability
trans_model = 1            # 0=trans from WUE, 1=Penman-Monteith, 2=Priestley-Taylor
fixleafnc = False          # fixed leaf N C ?
passiveconst = False       # hold passive pool at passivesoil
print_options = "daily"    # "daily"=every timestep, "end"=end of run
grazing = False            # Is foliage grazed?
use_eff_nc = 0             # use constant leaf n:c for  metfrac s
strfloat = 0               # Structural pool input N:C varies=1, fixed=0
use_leuning = 0    
fixed_stem_nc = True       # False=vary stem N:C with foliage, True=fixed stem N:C
deciduous_model = False    # evergreen_model=False, deciduous_model=True
calc_sw_params = False     # false=user supplies field capacity and wilting point, true=calculate them based on cosby et al.
water_stress = True        # water stress modifier turned on=1 (default)...ability to turn off to test things without drought stress = 0
modeljm = True             # modeljm=0, Jmax and Vcmax parameters are read in, modeljm=1, parameters are calculated from leaf N content
model_optroot = False      # Ross's optimal root model...not sure if this works yet...0=off, 1=on
soil_water_model = 0       # 0=Default based on Cosby parameters, 1=based on Landsberg and Waring. This version the curve is more gradual but the empirical basis is more questionable. Of course you could supply calibrated parameters!