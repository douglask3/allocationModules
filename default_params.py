"""
G'DAY default model parameters

Read into the model unless the user changes these at runtime with definitions
in the .INI file

"""

__author__  = "Martin De Kauwe"
__version__ = "1.0 (14.02.2011)"
__email__   = "mdekauwe@gmail.com"


# set environment parameters
finesoil          = 0.5            # clay+silt fraction

# set photosynthetic parameters
n_crit            = 0.04           # critical leaf n/c ratio for no prod n loss, Kirschbaum etal 1994, pg 1086, =0.016/0.45
kext              = 0.5            # extinction coefficient
slainit           = 3.9            # specific leaf area (m2 one-sided/kg DW)
slazero           = 3.9            # specific leaf area new fol at zero leaf N/C (m2 one-sided/kg DW)
slamax            = 3.9            # specofic leaf area new fol at max leaf N/C (m2 one-sided/kg DW)
lai_cover         = 0.5            # Onesided LAI correspdg to complete ground cover
cfracts           = 0.5            # carbon fraction of dry biomass
nmin              = 0.95           # minimum leaf n for +ve p/s (g/m2)
jmaxna            = 40.462         # slope of the reln btween jmax and leaf N content (g N m-2) - (umol/g n/s)
jmaxnb            = 13.691         # intercept of jmax vs n (umol/g n/s)
jmax              = -999.9         # maximum rate of electron transport (umol m-2 s-1)
vcmaxna           = 20.497         # slope of the reln btween vcmax and leaf N content (g N m-2) - (umol/g n/s)
vcmaxnb           = 8.403          # intercept of vcmax vs n (umol/g n/s)
vcmax             = -999.9         # maximum rate of carboxylation (umol m-2 s-1)
growth_efficiency = 0.7            # growth efficiency (yg)
alpha_j           = 0.3            # initial slope of rate of electron transport
alpha             = 0.05           # quantum yield (mol mol-1) used in mate
alpha0            = 0.05           # quantum efficiency at 20 degC. Sands 1996, pg 107
alpha1            = 0.016          # characterises strength of the temp dependance of alpha. Sands 1996, pg 107
direct_frac       = 0.5            # direct beam fraction of incident radiation
kq10              = 0.08           # exponential coefficient for Rm vs T
eav               = 51560.0        # Activation energy for Rubisco (J mol-1)
eaj               = 43790.0        # Activation energy for electron transport (J mol-1)
edj               = 2e+05          # Deactivation energy fro electron transport (J mol-1)
delsj             = 644.4338       # J mol-1 k-1
theta             = 0.7            # curvature of photosynthetic light response curve
gamstar25         = 42.75
Oi                = 205000.0       # intercellular concentration of O2 [umol mol-1]
Kc25              = 404.9          # Michaelis-Menten coefficents for carboxylation by Rubisco at 25degC [mmol mol-1]
Ko25              = 278400.0       # Michaelis-Menten coefficents for oxygenation by Rubisco at 25degC [umol mol-1]. Note value in Bernacchie 2001 is in mmol!!
Ec                = 79430.0        # Activation energy for carboxylation [J mol-1]
Eo                = 36380.0        # Activation energy for oxygenation [J mol-1]
Egamma            = 37830.0        # Activation energy at CO2 compensation point [J mol-1]
cue               = 0.5            # carbon use efficiency, or the ratio of NPP to GPP
g1                = 4.8            # fitted param, slope of reln btw gs and assimilation.

# set carbon allocation & grazing parameters
callocf          = 0.25  #allocation to leaves at leaf n_crit
callocfz         = 0.25  #allocation to leaves at zero leaf n/c
callocr          = 0.05  #allocation to roots at root n_crit
callocrz         = 0.05  #allocation to roots at zero root n/c
callocb          = 0.2   #allocation to branches at branch n_crit
callocbz         = 0.2   #allocation to branches at zero branch n/c
fracteaten       = 0.5   #Fractn of leaf prodn eaten by grazers
fracfaeces       = 0.3   #Fractn of grazd C that ends up in faeces (0..1)
ligfaeces        = 0.25  #Faeces lignin as fractn of biomass
faecescn         = 25.0  #Faeces C:N ratio
fractosoil       = 0.85  #Fractn of grazed N recycled to soil:faeces+urine
rhizresp         = 0.5   #0.33-0.67 C translocated from shoot to root is respired, so assume a value of 0.5 based on Lambers and Poot 2003.

#nitrogen cycling paramsa
rateuptake       = 5.7            # rate of N uptake from mineral N pool (/yr) from here? http://face.ornl.gov/Finzi-PNAS.pdf
rateloss         = 0.5            # Rate of N loss from mineral N pool (/yr)
fretrans         = 0.5            # foliage n retranslocation fraction
rretrans         = 0.0            # root n retranslocation fraction
bretrans         = 0.0            # branch n retranslocation fraction
wretrans         = 0.0            # mobile wood N retranslocation fraction
uo               = 2.737850787E-4 # Supply rate of available N (0.01 kg N m-2 yr-1 to t/ha/day)
kr               = 0.5            # N uptake coefficent (0.05 kg C m-2 to 0.5 tonnes/ha) see Silvia's PhD

#set nitrogen allocation parameters
ncwnewz          = 0.003          #New stem ring N:C at zero leaf N:C (mobile)
ncwnew           = 0.003          #New stem ring N:C at critical leaf N:C (mob)
ncwimmz          = 0.003          #Immobile stem N C at zero leaf N C
ncwimm           = 0.003          #Immobile stem N C at critical leaf N C
ncbnewz          = 0.003          #new branch N C at zero leaf N C
ncbnew           = 0.003          #new branch N C at critical leaf N C
ncrfac           = 0.8            #N:C of fine root prodn / N:C c of leaf prodn
ageold           = 1000.0         #Plant age when max leaf N C ratio is lowest
ageyoung         = 0.0            #Plant age when max leaf N C ratio is highest
ncmaxfyoung      = 0.04           #max N:C ratio of foliage in young stand, if the same as old=no effect
ncmaxfold        = 0.04           #max N:C ratio of foliage in old stand, if the same as young=no effect
ncmaxr           = 0.03           #max N:C ratio of roots
retransmob       = 0.0            #Fraction stem mobile N retranscd (/yr)
fhw              = 0.8            # n:c ratio of stemwood - immobile pool and new ring

#set litter parameters
fdecay           = 0.5            #foliage decay rate (1/yr)
fdecaydry        = 0.5            #Foliage decay rate - dry soil (1/yr)
rdecay           = 0.5            #root decay rate (1/yr)
rdecaydry        = 0.5            #root decay rate - dry soil (1/yr)
bdecay           = 0.03           #branch and large root decay rate (1/yr)
wdecay           = 0.02           #wood decay rate (1/yr)
watdecaydry      = 0.0            #water fractn for dry litterfall rates
watdecaywet      = 0.1            #water fractn for wet litterfall rates
ligshoot         = 0.25           #shoot litter lignin as fraction of c
ligroot          = 0.25           #root litter lignin as fraction of c
brabove          = 0.5            #above-ground fraction of branch pool litter
structcn         = 150.0          #C:N ratio of structural bit of litter input
structrat        = 0.0            #structural input n:c as fraction of metab

#set decomposition parameters - converted from yr to day in model!
kdec1            = 3.965571       #surface structural decay rate (1/yr)
kdec2            = 14.61          #surface metabolic decay rate (1/yr)
kdec3            = 4.904786       #soil structural decay rate (1/yr)
kdec4            = 18.262499      #soil metabolic decay rate(1/yr)
kdec5            = 7.305          #active pool decay rate (1/yr)
kdec6            = 0.198279       #slow pool decay rate (1/yr)
kdec7            = 0.006783       #passive pool decay rate (1/yr)

# Set N:C ratios of soil pools [units: g/m2]
actncmax         = 0.333333  # Active pool (=1/3) N:C ratio of new SOM - maximum [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
actncmin         = 0.066667  # Active pool (=1/15) N:C of new SOM - when Nmin=Nmin0 [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
slowncmax        = 0.066667  # Slow pool (=1/15) N:C ratio of new SOM - maximum [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
slowncmin        = 0.025     # Slow pool (=1/40) N:C of new SOM - when Nmin=Nmin0" [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
passncmax        = 0.142857  # Passive pool (=1/7) N:C ratio of new SOM - maximum [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
passncmin        = 0.1       # Passive pool (=1/10) N:C of new SOM - when Nmin=Nmin0 [units: gN/gC]. Based on forest version of CENTURY (Parton et al. 1993), see Appendix, McMurtrie 2001, Tree Physiology.
nmincrit         = 2.0       # Critical mineral N pool at max soil N:C (g/m2) (Parton et al 1993, McMurtrie et al 2001).
nmin0            = 0.0       # Mineral N pool corresponding to Actnc0,etc (g/m2)

#set water model parameters
wcapac_root       = 240.0 #Max plant avail soil water -root zone, i.e. total (mm) (smc_sat-smc_wilt) * root_depth (750mm) = [mm (water) / m (soil depth)]
wcapac_topsoil    = 100.0 #Max plant avail soil water -top soil (mm)
fwpmax_tsoil      = None  #Fractional water content at field capacity (max production). By default not set, values derived from Cosby eqns
fwpmin_tsoil      = None   #Fractional water content at wilting point (no production). By default not set, values derived from Cosby eqns
fwpmax_root       = None  #Fractional water content at field capacity (max production). By default not set, values derived from Cosby eqns
fwpmin_root       = None   #Fractional water content at wilting point (no production). By default not set, values derived from Cosby eqns
topsoil_type      = None
rootsoil_type     = None
fractup_soil      = 0.5   #fraction of uptake from top soil layer
extraction        = 0.007 #water extractn by unit root mass(ha/tC/d)
wetloss           = 0.5   #daily rainfall lost per lai (mm/day)
rfmult            = 1.0

# misc
latitude         = 39.11999 #latitude (degrees, negative for south)
albedo           = 0.18     #albedo
liteffnc         = 0.0
nuptakez = 0.0              # (1/yr)
passivesoilz = 1.0          # constant vals
passivesoilnz = 1.0         # constant vals
d0 = 0.0
d1 = 0.0
a1 = 0.0

# root model stuff
d0x = 0.35   # Length scale for exponential decline of Umax(z)
r0 = 0.1325 # root C at half-maximum N uptake (kg C/m3)
top_soil_depth = 0.3 # depth (cm) of soil assumed by G'DAY


# penman-monteith params
canht            = 17.0     # Canopy height (m)
dz0v_dh          = 0.123    # Rate of change of vegetation roughness length for momentum with height. Value from Jarvis? for conifer 0.075
displace_ratio   = 0.67     # Value for coniferous forest (0.78) from Jarvis et al 1976, taken from Jones 1992 pg 67. More standard assumption is 2/3
z0h_z0m          = 0.1      # Assume z0m = z0h, probably a big assumption [as z0h often < z0m.], see comment in code!! But 0.1 might be a better assumption

# decid model
ncfmin = 0.0151
previous_ncd = 17 # In the first year we don't have last years data, so I have precalculated the average of all the november-jan chilling values
store_transfer_len = None
#============== Not publicly accessible to the user ==========================#

# decay rates
decayrate = [None] * 7

# metabolic pool C fractions
fmfaeces = 0.0
fmleaf = 0.0
fmroot = 0.0
faecesn = 0.0

#==============================================================================#
