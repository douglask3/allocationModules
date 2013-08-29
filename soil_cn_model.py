""" Soil C and N flows into 4 litter pools (structural and metabolic, both
above and belowground) and 3 SOM pools (Active, slow and passive). In
essence the CENTURY model.

Active pool -> soil microbes and microbial products, turnover time of mths-yrs.
Slow pool -> resistant plant material, turnover time of 20-50 yrs.
Passive pool -> very resistant to decomp, turnover time of > 400 yrs.
"""

from math import exp
import sys
import constants as const
from utilities import float_eq, float_lt, float_le, float_gt, float_ge

__author__  = "Martin De Kauwe"
__version__ = "1.0 (28.08.2013)"
__email__   = "mdekauwe@gmail.com"


class CarbonSoilFlows(object):
    """ Plant litter C production is divided btw metabolic and structural """
    
    def __init__(self, control, params, state, fluxes, met_data):
        """
        Parameters
        ----------
        control : integers, object
            model control flags
        params: floats, object
            model parameters
        state: floats, object
            model state
        fluxes : floats, object
            model fluxes
        met_data : floats, dictionary
            meteorological forcing data

        """
        self.params = params
        self.fluxes = fluxes
        self.control = control
        self.state = state
        self.met_data = met_data
        
        # Fraction of C lost due to microbial respiration
        self.params.ft = 0.85 - (0.68 * self.params.finesoil)
        
    def calculate_csoil_flows(self, project_day):
        """ C from decomposing litter -> active, slow and passive SOM pools.

        Parameters:
        -----------
        project_day : integer
            simulation day

        """
        # calculate model decay rates
        self.calculate_decay_rates(project_day)

        # plant litter inputs to the metabolic and structural pools determined 
        # by ratio of lignin/N ratio 
        (lnleaf, lnroot) = self.ligin_nratio()
        self.params.fmleaf = self.metafract(lnleaf)
        self.params.fmroot = self.metafract(lnroot)
        
        self.flux_from_grazers() # input from faeces
        self.partition_plant_litter()
        self.cfluxes_from_structural_pool()
        self.cfluxes_from_metabolic_pool()
        self.cfluxes_from_active_pool()
        self.cfluxes_from_slow_pool()
        self.cfluxes_from_passive_pool()
        self.fluxes.hetero_resp = self.calculate_soil_respiration()
        
        # update the C pools
        self.calculate_cpools()
        
        # calculate NEP
        self.fluxes.nep = (self.fluxes.npp - self.fluxes.hetero_resp -
                           self.fluxes.ceaten * (1.0 - self.params.fracfaeces))
        
    def calculate_decay_rates(self, project_day):
        """ Model decay rates - decomposition rates have a strong temperature 
        and moisture dependency. Note same temperature is assumed for all 3 
        SOM pools, found by Knorr et al (2005) to be untrue. N mineralisation
        depends on top soil moisture (most variable) (Connell et al. 1995)
        
        References:
        -----------
        Knorr et al. (2005) Nature, 433, 298-301.
        Connell et al. (1995) Biol. Fert. Soils, 20, 213-220.
    
        Parameters:
        -----------
        project_day : int
            current simulation day (index)

        """
        
        # abiotic decomposition factor - impact of soil moisture 
        # and soil temperature on microbial activity
        adfac = self.state.wtfac_tsoil * self.soil_temp_factor(project_day)
        
        # Effect of soil texture (silt + clay content) on active SOM turnover
        # -> higher turnover for sandy soils
        soil_text = 1.0 - (0.75 * self.params.finesoil)
        
        # Impact of lignin content
        lignin_cont_leaf = exp(-3.0 * self.params.ligshoot)
        lignin_cont_root = exp(-3.0 * self.params.ligroot)
        
        # decay rate of surface structural pool
        self.params.decayrate[0] = self.params.kdec1 * lignin_cont_leaf * adfac
                                   
        # decay rate of surface metabolic pool
        self.params.decayrate[1] = self.params.kdec2 * adfac

        # decay rate of soil structural pool
        self.params.decayrate[2] = self.params.kdec3 * lignin_cont_root * adfac

        # decay rate of soil metabolic pool
        self.params.decayrate[3] = self.params.kdec4 * adfac

        # decay rate of active pool
        self.params.decayrate[4] = self.params.kdec5 * soil_text * adfac
                                        
        # decay rate of slow pool
        self.params.decayrate[5] = self.params.kdec6 * adfac

        # decay rate of passive pool
        self.params.decayrate[6] = self.params.kdec7 * adfac

    def soil_temp_factor(self, project_day):
        """Soil-temperature activity factor (A9). Fit to Parton's fig 2a 

        Parameters:
        -----------
        project_day : int
            current simulation day (index)

        Returns:
        --------
        tfac : float
            soil temperature factor [degC]

        """
        tsoil = self.met_data['tsoil'][project_day]

        if float_gt(tsoil, 0.0):
            tfac = (0.0326 + 0.00351 * tsoil**1.652 - (tsoil / 41.748)**7.19)
            if float_lt(tfac, 0.0):
                tfac = 0.0
        else:
            # negative number cannot be raised to a fractional power
            # number would need to be complex
            tfac = 0.0

        return tfac
    
    def flux_from_grazers(self):
        """ Input from faeces """
        if self.control.grazing:
            arg = (self.params.ligfaeces * self.params.faecescn /
                   self.params.cfracts)
            self.params.fmfaeces = self.metafract(arg)
            self.fluxes.faecesc = self.fluxes.ceaten * self.params.fracfaeces
        else:
            self.params.fmfaeces = 0.0
            self.fluxes.faecesc = 0.0

    def ligin_nratio(self):
        """ Estimate Lignin/N ratio, as this dictates the how plant litter is 
        seperated between metabolic and structural pools.

        Returns:
        --------
        lnleaf : float
            lignin:N ratio of leaf
        lnroot : float
            lignin:N ratio of fine root
        """
        nc_leaf_litter = self.ratio_of_litternc_to_live_leafnc()
        nc_root_litter = self.ratio_of_litternc_to_live_rootnc()
        
        if float_eq(nc_leaf_litter, 0.0):
            # catch divide by zero if we have no leaves 
            lnleaf = 0.0 
        else:
            lnleaf = self.params.ligshoot / self.params.cfracts / nc_leaf_litter
            #print self.params.ligshoot

        if float_eq(nc_root_litter, 0.0):
            # catch divide by zero if we have no roots
            lnroot = 0.0 
        else:
            lnroot = self.params.ligroot / self.params.cfracts / nc_root_litter

        return (lnleaf, lnroot)

    def ratio_of_litternc_to_live_leafnc(self):
        """ratio of litter N:C to live leaf N:C

        Returns:
        --------
        nc_leaf_litter : float
            N:C ratio of litter to foliage

        """
        if self.control.use_eff_nc:
            nc_leaf_litter = self.params.liteffnc * (1.0 - self.params.fretrans)
        else:
            if float_eq(self.fluxes.deadleaves, 0.0):
                nc_leaf_litter = 0.0
            else:
                nc_leaf_litter = self.fluxes.deadleafn / self.fluxes.deadleaves

        return nc_leaf_litter


    def ratio_of_litternc_to_live_rootnc(self):
        """ratio of litter N:C to live root N:C

        Returns:
        --------
        nc_root_litter : float
            N:C ratio of litter to live root

        """
        if self.control.use_eff_nc:
            nc_root_litter = (self.params.liteffnc * self.params.ncrfac *
                             (1.0 - self.params.rretrans))
        else:
            if float_eq(self.fluxes.deadroots, 0.0):
                nc_root_litter = 0.0
            else:
                nc_root_litter = self.fluxes.deadrootn / self.fluxes.deadroots

        return nc_root_litter

    def metafract(self, lig2n):
        """ Calculate what fraction of the litter will be partitioned to the 
        metabolic pool which is given by the lignin:N ratio.

        Parameters:
        -----------
        lig2n : float
            lignin to N ratio

        Returns:
        --------
        metabolic fraction : float
            partitioned fraction to metabolic pool [must be positive]
        """
        
        # At least 2% goes to metabolic in CENTURY 4 code and as stated in
        # Nalder and Wein (1996) Ecological Modelling, 192, 37-66, which is 
        # presumably based on CENTURY 4 codebase.
        #return max(0.2, 0.85 - (0.018 * lig2n))
        
        return max(0.0, 0.85 - (0.018 * lig2n))
    
    def partition_plant_litter(self):
        """ Partition litter from the plant (surface) and roots into metabolic
        and structural pools  """
        
        #
        # Surface (leaves, branches, stem) Litter
        #
        
        # -> structural
        self.fluxes.surf_struct_litter = (self.fluxes.deadleaves *
                                         (1.0 - self.params.fmleaf) +
                                          self.fluxes.deadbranch * 
                                          self.params.brabove +
                                          self.fluxes.deadstems + 
                                          self.fluxes.faecesc *
                                          (1.0 - self.params.fmfaeces))

        # -> metabolic 
        self.fluxes.surf_metab_litter = (self.fluxes.deadleaves * 
                                         self.params.fmleaf +
                                         self.fluxes.faecesc * 
                                         self.params.fmfaeces) 
        #
        # Root Litter
        #
        
        # -> structural
        self.fluxes.soil_struct_litter = (self.fluxes.deadroots *
                                         (1.0 - self.params.fmroot) +
                                          self.fluxes.deadbranch *
                                         (1.0 - self.params.brabove))
        # -> metabolic
        self.fluxes.soil_metab_litter = (self.fluxes.deadroots * 
                                         self.params.fmroot)

    def cfluxes_from_structural_pool(self):
        """C fluxes from structural pools """

        structout_surf = self.state.structsurf * self.params.decayrate[0]
        structout_soil = self.state.structsoil * self.params.decayrate[2]
        ligshoot = self.params.ligshoot
        ligroot = self.params.ligroot
        
        # C flux surface structural pool -> slow pool
        self.fluxes.surf_struct_to_slow = structout_surf * ligshoot * 0.7
        
        # C flux surface structural pool -> active pool
        self.fluxes.surf_struct_to_active = (structout_surf * 
                                            (1.0 - ligshoot) * 0.55)
        
        # C flux soil structural pool -> slow pool
        self.fluxes.soil_struct_to_slow = structout_soil * ligroot * 0.7
        
        # soil structural pool -> active pool
        self.fluxes.soil_struct_to_active = (structout_soil * 
                                            (1.0 - ligroot) * 0.45)
        
    
        # Respiration fluxes
        
        # CO2 lost during transfer of structural C to the slow pool
        self.fluxes.co2_to_air[0] = (structout_surf * 
                                    (ligshoot * 0.3 + (1.0 - ligshoot) * 0.45))
        
        # CO2 lost during transfer structural C  to the active pool
        self.fluxes.co2_to_air[1] = (structout_soil * 
                                    (ligroot * 0.3 + (1.0 - ligroot) * 0.55))

    def cfluxes_from_metabolic_pool(self):
        """C fluxes from metabolic pools """
       
        # C flux surface metabolic pool -> active pool
        self.fluxes.surf_metab_to_active = (self.state.metabsurf *
                                            self.params.decayrate[1] * 0.45)
        
        # C flux soil metabolic pool  -> active pool
        self.fluxes.soil_metab_to_active = (self.state.metabsoil *
                                            self.params.decayrate[3] * 0.45)
    
        # Respiration fluxes 
        self.fluxes.co2_to_air[2] = (self.state.metabsurf *
                                     self.params.decayrate[1] * 0.55)
        
        self.fluxes.co2_to_air[3] = (self.state.metabsoil *
                                     self.params.decayrate[3] * 0.55)
        
        
    def cfluxes_from_active_pool(self):
        """C fluxes from active pools """
        
        activeout = self.state.activesoil * self.params.decayrate[4]
        
        # C flux active pool -> slow pool
        self.fluxes.active_to_slow = activeout * (1.0 - self.params.ft - 0.004)
        #self.fluxes.active_to_slow = (activeout * 
        #                             (1.0 - self.params.ft - 0.003 - 
        #                              0.032 * Claysoil)) # (Parton 1993)
        
        # C flux active pool -> passive pool
        self.fluxes.active_to_passive = activeout * 0.004
        
        # Respiration fluxes
        self.fluxes.co2_to_air[4] = activeout * self.params.ft    
    
    def cfluxes_from_slow_pool(self):
        """C fluxes from slow pools """
        
        slowout = self.state.slowsoil * self.params.decayrate[5]
        
        # C flux slow pool -> active pool
        self.fluxes.slow_to_active = slowout * 0.42
        
        # slow pool -> passive pool
        self.fluxes.slow_to_passive = slowout * 0.03
        
        # Respiration fluxes
        self.fluxes.co2_to_air[5] = slowout * 0.55
    
    def cfluxes_from_passive_pool(self):
        """ C fluxes from passive pool """
       
        # C flux passive pool -> active pool
        self.fluxes.passive_to_active = (self.state.passivesoil *
                                         self.params.decayrate[6] * 0.45)
    
        # Respiration fluxes
        self.fluxes.co2_to_air[6] = (self.state.passivesoil *
                                     self.params.decayrate[6] * 0.55)

    
    def calculate_soil_respiration(self):
        """ calculate the total soil respiration (heterotrophic) flux, i.e. 
        the amount of CO2 released back to the atmosphere """
        
        soil_resp = sum(self.fluxes.co2_to_air)
        
        # insert following line so value of respiration obeys c conservation if 
        # assuming a fixed passive pool
        if self.control.passiveconst == True:
            soil_resp = (self.fluxes.hetero_resp +
                         self.fluxes.active_to_passive +
                         self.fluxes.slow_to_passive -
                         self.state.passivesoil *
                         self.params.decayrate[6])
       
        return soil_resp
    
    def calculate_cpools(self):
        """Calculate new soil carbon pools. """
        
        # store the C SOM fluxes for Nitrogen calculations
        self.fluxes.c_into_active = (self.fluxes.surf_struct_to_active + 
                                     self.fluxes.soil_struct_to_active +
                                     self.fluxes.surf_metab_to_active + 
                                     self.fluxes.soil_metab_to_active +
                                     self.fluxes.slow_to_active +
                                     self.fluxes.passive_to_active)
        
        self.fluxes.c_into_slow = (self.fluxes.surf_struct_to_slow + 
                                   self.fluxes.soil_struct_to_slow +
                                   self.fluxes.active_to_slow)
        
        self.fluxes.c_into_passive = (self.fluxes.active_to_passive + 
                                      self.fluxes.slow_to_passive)
        
        
        # update pools
        self.state.structsurf += (self.fluxes.surf_struct_litter - 
                                 (self.fluxes.surf_struct_to_slow +
                                  self.fluxes.surf_struct_to_active +
                                  self.fluxes.co2_to_air[0]))
                                  
        self.state.structsoil += (self.fluxes.soil_struct_litter - 
                                 (self.fluxes.soil_struct_to_slow +
                                  self.fluxes.soil_struct_to_active +
                                  self.fluxes.co2_to_air[1]))
        
        # When nothing is being added to the metabolic pools, there is the 
        # potential scenario with the way the model works for tiny bits to be
        # removed with each timestep. Effectively with time this value which is
        # zero can end up becoming zero but to a silly decimal place
        self.state.metabsurf += (self.fluxes.surf_metab_litter - 
                                (self.fluxes.surf_metab_to_active +
                                 self.fluxes.co2_to_air[2]))
                                 
        self.state.metabsoil += (self.fluxes.soil_metab_litter - 
                                (self.fluxes.soil_metab_to_active +
                                 self.fluxes.co2_to_air[3]))
                                 
        self.state.activesoil += (self.fluxes.c_into_active - 
                                 (self.fluxes.active_to_slow +
                                  self.fluxes.active_to_passive +
                                  self.fluxes.co2_to_air[4]))
                                  
        self.state.slowsoil += (self.fluxes.c_into_slow - 
                               (self.fluxes.slow_to_active +
                                self.fluxes.slow_to_passive +
                                self.fluxes.co2_to_air[5]))
                                
        self.state.passivesoil += (self.fluxes.c_into_passive - 
                                  (self.fluxes.passive_to_active +
                                   self.fluxes.co2_to_air[6]))
        
        # When nothing is being added to the metabolic pools, there is the 
        # potential scenario with the way the model works for tiny bits to be
        # removed with each timestep. Effectively with time this value which is
        # zero can end up becoming zero but to a silly decimal place
        self.precision_control()
        
    def precision_control(self, tolerance=1E-08):
        """ Detect very low values in state variables and force to zero to 
        avoid rounding and overflow errors """       
        
        # C & N state variables 
        if self.state.metabsurf < tolerance:
            excess = self.state.metabsurf
            self.fluxes.surf_metab_to_active = excess * 0.45 # to active pool
            self.fluxes.co2_to_air[2] = excess * 0.55 # to air
            self.state.metabsurf = 0.0
        
       
        if self.state.metabsoil < tolerance:
            excess = self.state.metabsoil
            self.fluxes.soil_metab_to_active = excess * 0.45 # to active pool
            self.fluxes.co2_to_air[3] = excess * 0.55 # to air
            self.state.metabsoil = 0.0  
       
                    
class NitrogenSoilFlows(object):
    """ Calculate daily nitrogen fluxes"""
    def __init__(self, control, params, state, fluxes, met_data):
        """
        Parameters
        ----------
        control : integers, object
            model control flags
        params: floats, object
            model parameters
        state: floats, object
            model state
        fluxes : floats, object
            model fluxes

        """
        self.params = params
        self.fluxes = fluxes
        self.control = control
        self.state = state
        self.met_data = met_data

    def calculate_nsoil_flows(self, project_day):
        
        self.fluxes.ninflow = self.met_data['ndep'][project_day]
        
        self.grazer_inputs()
        (nsurf, nsoil) = self.inputs_from_plant_litter()
        self.partition_plant_litter_n(nsurf, nsoil)

        

        # SOM nitrogen effluxes.  These are assumed to have the source n:c
        # ratio prior to the increase of N:C due to co2 evolution.
        self.nfluxes_from_structural_pools()
        self.nfluxes_from_metabolic_pool()
        self.nfluxes_from_active_pool()
        self.nfluxes_from_slow_pool()
        self.nfluxes_from_passive_pool()
        
        # gross N mineralisation 
        self.fluxes.ngross = self.calculate_n_mineralisation()
        
        # calculate N immobilisation
        self.fluxes.nimmob = self.calculate_n_immobilisation()
        
        # Update model soil N pools
        self.calculate_npools()
        
        # calculate N net mineralisation
        self.fluxes.nmineralisation = self.calc_net_mineralisation()
        
    def grazer_inputs(self):
        """ Grazer inputs from faeces and urine, flux detd by faeces c:n """
        if self.control.grazing:
            self.params.faecesn = self.fluxes.faecesc / self.params.faecescn
        else:
            self.params.faecesn = 0.0

        # make sure faecesn <= total n input to soil from grazing
        arg = self.fluxes.neaten * self.params.fractosoil
        if float_gt(self.params.faecesn, arg):
            self.params.faecesn = self.fluxes.neaten * self.params.fractosoil

        # urine=total-faeces
        if self.control.grazing:
            self.fluxes.nurine = (self.fluxes.neaten * self.params.fractosoil -
                                  self.params.faecesn)
        else:
            self.fluxes.nurine = 0.0

        if float_lt(self.fluxes.nurine, 0.0):
            self.fluxes.nurine = 0.0

    def inputs_from_plant_litter(self):
        """ inputs from plant litter.

        surface and soil pools are independent. Structural input flux n:c can
        be either constant or a fixed fraction of metabolic input flux.

        Returns:
        --------
        nsurf : float
            N input from surface pool
        nsoil : float
            N input from soil pool

        """
        # surface and soil inputs (faeces n goes to abovgrd litter pools)
        nsurf = (self.fluxes.deadleafn + self.fluxes.deadbranchn *
                 self.params.brabove + self.fluxes.deadstemn +
                 self.params.faecesn)
        
        nsoil = (self.fluxes.deadrootn + self.fluxes.deadbranchn *
                (1.0 - self.params.brabove))

        return nsurf, nsoil
    
    def partition_plant_litter_n(self, nsurf, nsoil):
        """ Partition litter N from the plant (surface) and roots into metabolic
        and structural pools  
        
        Parameters:
        -----------
        nsurf : float
            N input from surface pool
        nsoil : float
            N input from soil pool
        """
        # constant structural input n:c as per century
        if not self.control.strfloat:
        
            # dead plant litter -> structural pool

            # n flux -> surface structural pool
            self.fluxes.n_surf_struct_litter = (self.fluxes.surf_struct_litter / 
                                                self.params.structcn)
            # n flux -> soil structural pool
            self.fluxes.n_soil_struct_litter = (self.fluxes.soil_struct_litter / 
                                                self.params.structcn)                         
                                     
            # if not enough N for structural, all available N goes to structural
            if float_gt( self.fluxes.n_surf_struct_litter, nsurf):
                 self.fluxes.n_surf_struct_litter = nsurf
            if float_gt(self.fluxes.n_soil_struct_litter, nsoil):
                self.fluxes.n_soil_struct_litter = nsoil
        
        # structural input n:c is a fraction of metabolic
        else:
            c_surf_struct_litter = (self.fluxes.surf_struct_litter * 
                                    self.params.structrat +
                                    self.fluxes.surf_metab_litter)
            
            if float_eq(c_surf_struct_litter, 0.0):
                 self.fluxes.n_surf_struct_litter = 0.0
            else:
                 self.fluxes.n_surf_struct_litter = (nsurf * 
                                              self.fluxes.surf_struct_litter *
                                              self.params.structrat / 
                                              c_surf_struct_litter)
            
            c_soil_struct_litter = (self.fluxes.soil_struct_litter * 
                                    self.params.structrat +
                                    self.fluxes.soil_metab_litter)
           
            if float_eq(c_soil_struct_litter, 0.0):
                self.fluxes.n_soil_struct_litter = 0.
            else:
                self.fluxes.n_soil_struct_litter = (nsurf * 
                                                    self.fluxes.soil_struct_litter *
                                                    self.params.structrat / 
                                                    c_soil_struct_litter)
        
        # remaining N goes to metabolic pools
        self.fluxes.n_surf_metab_litter = (nsurf - 
                                           self.fluxes.n_surf_struct_litter)
        self.fluxes.n_soil_metab_litter = (nsoil - 
                                           self.fluxes.n_soil_struct_litter)
    
    def nfluxes_from_structural_pools(self):
        """ from structural pool """
        structout_surf = self.state.structsurfn * self.params.decayrate[0]
        structout_soil = self.state.structsoiln * self.params.decayrate[2]
        ligshoot = self.params.ligshoot
        ligroot = self.params.ligroot
        
        sigwt = (structout_surf / 
                (ligshoot * 0.7 + (1.0 - ligshoot) * 0.55))
        
        # N flux from surface structural pool -> slow pool
        self.fluxes.n_surf_struct_to_slow = sigwt * ligshoot * 0.7
        
        # N flux surface structural pool -> active pool
        self.fluxes.n_surf_struct_to_active = sigwt * (1.0 - ligshoot) * 0.55
        
        sigwt = structout_soil / (ligroot * 0.7 + (1. - ligroot) * 0.45)
        
        
        # N flux from soil structural pool -> slow pool
        self.fluxes.n_soil_struct_to_slow = sigwt * ligroot * 0.7
        
        # N flux from soil structural pool -> active pool
        self.fluxes.n_soil_struct_to_active = sigwt * (1.0 - ligroot) * 0.45
    
    def nfluxes_from_metabolic_pool(self):
        """ N fluxes from metabolic pool"""
       
        # N flux surface metabolic pool -> active pool
        self.fluxes.n_surf_metab_to_active = (self.state.metabsurfn *
                                              self.params.decayrate[1])
        
        # N flux soil metabolic pool  -> active pool
        self.fluxes.n_soil_metab_to_active = (self.state.metabsoiln *
                                              self.params.decayrate[3])
    
    def nfluxes_from_active_pool(self):
        """ N fluxes from active pool """
        activeout = self.state.activesoiln * self.params.decayrate[4]
        sigwt = activeout / (1. - self.params.ft)

        # N flux active pool -> slow pool
        self.fluxes.n_active_to_slow = sigwt * (1. - self.params.ft - 0.004)

        # N flux active pool -> passive pool
        self.fluxes.n_active_to_passive = sigwt * 0.004
        
    def nfluxes_from_slow_pool(self):
        """N fluxes from slow pools """
        
        slowout = self.state.slowsoiln * self.params.decayrate[5]
        sigwt = slowout / 0.45
        
        # C flux slow pool -> active pool
        self.fluxes.n_slow_to_active = sigwt * 0.42
        
        # slow pool -> passive pool
        self.fluxes.n_slow_to_passive = sigwt * 0.03
    
    def nfluxes_from_passive_pool(self):
        """ N fluxes from passive pool """
       
        # C flux passive pool -> active pool
        self.fluxes.n_passive_to_active = (self.state.passivesoiln *
                                           self.params.decayrate[6])

    def calculate_n_mineralisation(self):
        """ N gross mineralisation rate is given by the excess of N outflows 
        over inflows. Nitrogen mineralisation is the process by which organic 
        N is converted to plant available inorganic N, i.e. microbes decompose
        organic N from organic matter to ammonia (NH3) and ammonium (NH4), 
        called ammonification.
        
        Returns:
        --------
        value : float
            Gross N mineralisation 
        """
        return (self.fluxes.n_surf_struct_to_slow +
                self.fluxes.n_surf_struct_to_active +
                self.fluxes.n_soil_struct_to_slow +
                self.fluxes.n_soil_struct_to_active +
                self.fluxes.n_surf_metab_to_active + 
                self.fluxes.n_soil_metab_to_active +
                self.fluxes.n_active_to_slow +
                self.fluxes.n_active_to_passive +
                self.fluxes.n_slow_to_active +
                self.fluxes.n_slow_to_passive +
                self.fluxes.n_passive_to_active)
    
    def calculate_n_immobilisation(self):
        """ N immobilised in new soil organic matter, the reverse of
        mineralisation. Micro-organisms in the soil compete with plants for N.
        Immobilisation is the process by which nitrate and ammonium are taken up
        by the soil organisms and thus become unavailable to the plant 
        (->organic N).
        
        When C:N ratio is high the microorganisms need more nitrogen from 
        the soil to decompose the carbon in organic materials. This N will be
        immobilised until these microorganisms die and the nitrogen is 
        released.
        
        General equation for new soil N:C ratio vs Nmin, expressed as linear 
        equation passing through point Nmin0, actncmin (etc). Values can be 
        Nmin0=0, Actnc0=Actncmin 

        if Nmin < Nmincrit:
            New soil N:C = soil N:C (when Nmin=0) + slope * Nmin

        if Nmin > Nmincrit
            New soil N:C = max soil N:C       
        
        NB N:C ratio of new passive SOM can change even if assume Passiveconst
        
        Returns:
        --------
        nimob : float
            N immobilsed
        """
        # N:C new SOM - active, slow and passive
        self.state.actncslope = self.calculate_nc_slope(self.params.actncmax, 
                                                        self.params.actncmin)
        self.state.slowncslope = self.calculate_nc_slope(self.params.slowncmax, 
                                                         self.params.slowncmin)
        self.state.passncslope = self.calculate_nc_slope(self.params.passncmax, 
                                                         self.params.passncmin) 

        nmin = self.params.nmin0 * const.G_M2_2_TONNES_HA
        arg1 = ((self.fluxes.active_to_passive + self.fluxes.slow_to_passive) *
                (self.params.passncmin - self.state.passncslope * nmin))
        arg2 = ((self.fluxes.surf_struct_to_slow + 
                 self.fluxes.soil_struct_to_slow +
                 self.fluxes.active_to_slow) *
                (self.params.slowncmin - self.state.slowncslope * nmin))
        arg3 = ((self.fluxes.surf_struct_to_active + 
                 self.fluxes.soil_struct_to_active +
                 self.fluxes.surf_metab_to_active + 
                 self.fluxes.soil_metab_to_active +
                 self.fluxes.slow_to_active +
                 self.fluxes.passive_to_active) * 
                 (self.params.actncmin - self.state.actncslope * nmin))
        numer1 = arg1 + arg2 + arg3
        
        arg1 = ((self.fluxes.active_to_passive + self.fluxes.slow_to_passive) *
                 self.params.passncmax)
        arg2 = ((self.fluxes.surf_struct_to_slow + 
                 self.fluxes.soil_struct_to_slow +
                 self.fluxes.active_to_slow) * self.params.slowncmax)
        arg3 = ((self.fluxes.surf_struct_to_active + 
                 self.fluxes.soil_struct_to_active +
                 self.fluxes.surf_metab_to_active + 
                 self.fluxes.soil_metab_to_active +
                 self.fluxes.slow_to_active +
                 self.fluxes.passive_to_active) * 
                 self.params.actncmax)
        numer2 = arg1 + arg2 + arg3

        arg1 = ((self.fluxes.active_to_passive + self.fluxes.slow_to_passive) * 
                 self.state.passncslope)
        arg2 = ((self.fluxes.surf_struct_to_slow + 
                 self.fluxes.soil_struct_to_slow +
                 self.fluxes.active_to_slow) * 
                 self.state.slowncslope)
        arg3 = ((self.fluxes.surf_struct_to_active + 
                 self.fluxes.soil_struct_to_active +
                 self.fluxes.surf_metab_to_active + 
                 self.fluxes.soil_metab_to_active +
                 self.fluxes.slow_to_active +
                 self.fluxes.passive_to_active) * 
                 self.state.actncslope)
        denom = arg1 + arg2 + arg3
        
        # evaluate N immobilisation in new SOM
        nimmob = numer1 + denom * self.state.inorgn
        if float_gt(nimmob, numer2):
            nimmob = numer2
        
        return nimmob
    
    def calc_net_mineralisation(self):
        """ N Net mineralisation, i.e. excess of N outflows over inflows """
        return (self.fluxes.ninflow + self.fluxes.ngross - self.fluxes.nimmob +
                self.fluxes.nlittrelease)
    
    def calculate_nc_slope(self, pool_ncmax, pool_ncmin):
        """ Returns N:C ratio of the mineral pool slope """
        arg1 = (pool_ncmax - pool_ncmin)
        arg2 = ((self.params.nmincrit - self.params.nmin0) * 
                 const.G_M2_2_TONNES_HA)
        
        return arg1 / arg2 
    
    def calculate_npools(self):
        """ Calculate new soil N pools. """

        # net source fluxes.
        self.fluxes.n_into_active = (self.fluxes.n_surf_struct_to_active + 
                                     self.fluxes.n_soil_struct_to_active +
                                     self.fluxes.n_surf_metab_to_active + 
                                     self.fluxes.n_soil_metab_to_active +
                                     self.fluxes.n_slow_to_active + 
                                     self.fluxes.n_passive_to_active)
        
        self.fluxes.n_into_slow = (self.fluxes.n_surf_struct_to_slow + 
                                   self.fluxes.n_soil_struct_to_slow +
                                   self.fluxes.n_active_to_slow)
                                   
        self.fluxes.n_into_passive = (self.fluxes.n_active_to_passive + 
                                      self.fluxes.n_slow_to_passive)

        
        # Update N soil pools
        
        # net N release implied by separation of litter into structural
        # & metabolic. The following pools only fix or release N at their 
        # limiting n:c values. 
        
        # N released or fixed from the N inorganic pool is incremented with
        # each call to nclimit and stored in self.fluxes.nlittrelease
        self.fluxes.nlittrelease = 0.0
        
        self.state.structsurfn += (self.fluxes.n_surf_struct_litter - 
                                  (self.fluxes.n_surf_struct_to_slow + 
                                   self.fluxes.n_surf_struct_to_active))
                                   
        if not self.control.strfloat:
            self.state.structsurfn += self.nclimit(self.state.structsurf,
                                                   self.state.structsurfn,
                                                   1.0/self.params.structcn,
                                                   1.0/self.params.structcn)
        
        self.state.structsoiln += (self.fluxes.n_soil_struct_litter - 
                                  (self.fluxes.n_soil_struct_to_slow + 
                                   self.fluxes.n_soil_struct_to_active))
                                  
        if not self.control.strfloat:
            self.state.structsoiln += self.nclimit(self.state.structsoil,
                                                   self.state.structsoiln,
                                                   1.0/self.params.structcn,
                                                   1.0/self.params.structcn)
        
        self.state.metabsurfn += (self.fluxes.n_surf_metab_litter - 
                                  self.fluxes.n_surf_metab_to_active)
        self.state.metabsurfn += self.nclimit(self.state.metabsurf,
                                              self.state.metabsurfn,
                                              1.0/25.0, 1.0/10.0)
        
        self.state.metabsoiln += (self.fluxes.n_soil_metab_litter - 
                                  self.fluxes.n_soil_metab_to_active)
        self.state.metabsoiln += self.nclimit(self.state.metabsoil,
                                              self.state.metabsoiln,
                                              1.0/25.0, 1.0/10.0)
        
        # When nothing is being added to the metabolic pools, there is the 
        # potential scenario with the way the model works for tiny bits to be
        # removed with each timestep. Effectively with time this value which is
        # zero can end up becoming zero but to a silly decimal place
        self.precision_control()
        
        # N:C of the SOM pools increases linearly btw prescribed min and max 
        # values as the Nconc of the soil increases.
        arg = (self.state.inorgn - self.params.nmin0 / const.M2_AS_HA * 
                const.G_AS_TONNES)
        # active
        actnc = self.params.actncmin + self.state.actncslope * arg
        if float_gt(actnc, self.params.actncmax):
            actnc = self.params.actncmax
        fixn = ncflux(self.fluxes.c_into_active, self.fluxes.n_into_active, 
                      actnc)
        self.state.activesoiln += (self.fluxes.n_into_active + fixn - 
                                  (self.fluxes.n_active_to_slow + 
                                   self.fluxes.n_active_to_passive))

        # slow
        slownc = self.params.slowncmin + self.state.slowncslope * arg
        if float_gt(slownc, self.params.slowncmax):
            slownc = self.params.slowncmax
        fixn = ncflux(self.fluxes.c_into_slow, self.fluxes.n_into_slow, slownc)
        self.state.slowsoiln += (self.fluxes.n_into_slow + fixn - 
                                (self.fluxes.n_slow_to_active + 
                                 self.fluxes.n_slow_to_passive))

        # passive
        passnc = self.params.passncmin + self.state.passncslope * arg
        if float_gt(passnc, self.params.passncmax):
            passnc = self.params.passncmax
        fixn = ncflux(self.fluxes.c_into_passive, self.fluxes.n_into_passive, 
                      passnc)
        # update passive pool only if passiveconst=0
        self.state.passivesoiln += (self.fluxes.n_into_passive + fixn - 
                                    self.fluxes.n_passive_to_active)

        # Daily increment of soil inorganic N pool, diff btw in and effluxes
        # (grazer urine n goes directly into inorganic pool) nb inorgn may be
        # unstable if rateuptake is large
        self.state.inorgn += ((self.fluxes.ngross + self.fluxes.ninflow + 
                               self.fluxes.nurine - self.fluxes.nimmob - 
                               self.fluxes.nloss - self.fluxes.nuptake) + 
                               self.fluxes.nlittrelease)
        
    def nclimit(self, cpool, npool, ncmin, ncmax):
        """ Release N to 'Inorgn' pool or fix N from 'Inorgn', in order to keep
        the  N:C ratio of a litter pool within the range 'ncmin' to 'ncmax'.

        Parameters:
        -----------
        cpool : float
            various C pool (state)
        npool : float
            various N pool (state)
        ncmin : float
            maximum N:C ratio
        ncmax : float
            minimum N:C ratio

        Returns:
        --------
        fix/rel : float
            amount of N to be added/released from the inorganic pool

        """
        nmax = cpool * ncmax
        nmin = cpool * ncmin
    
        if float_gt(npool, nmax):  #release
            rel = npool - nmax
            self.fluxes.nlittrelease += rel 
            return -rel
        elif float_lt(npool, nmin):   #fix
            fix = nmin - npool
            self.fluxes.nlittrelease -= fix
            return fix
        else:
            return 0.0 
    
    def precision_control(self, tolerance=1E-08):
        """ Detect very low values in state variables and force to zero to 
        avoid rounding and overflow errors """       
        
        if self.state.metabsurfn < tolerance:
            excess = self.state.metabsurfn
            self.fluxes.n_surf_metab_to_active = excess 
            self.state.metabsurfn = 0.0
       
        if self.state.metabsoiln < tolerance:
            excess = self.state.metabsoiln
            self.fluxes.n_soil_metab_to_active = excess 
            self.state.metabsoiln = 0.0

def ncflux(cflux, nflux, nc_ratio):
    """Returns the amount of N fixed

    Release N to Inorgn or fix N from Inorgn, in order to normalise
    the N: C ratio of a net flux.
    """
    return cflux * nc_ratio - nflux