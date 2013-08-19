""" Estimate daily Carbon fixed and pass around the aboveground portion of the
plant. """
import sys
from math import exp, log
import sys
import constants as const
from utilities import float_eq, float_lt, float_gt
from bewdy import Bewdy
from water_balance import WaterBalance, SoilMoisture
from mate import Mate
from optimal_root_model import RootingDepthModel
from utilities import Simplemovingaverage

__author__  = "Martin De Kauwe"
__version__ = "1.0 (23.02.2011)"
__email__   = "mdekauwe@gmail.com"


class PlantGrowth(object):
    """ G'DAY plant growth module.

    Calls photosynthesis model, water balance and evolve plant state.
    Pools recieve C through allocation of accumulated photosynthate and N
    from both soil uptake and retranslocation within the plant.

    Key feedback through soil N mineralisation and plant N uptake

    * Note met_forcing is an object with radiation, temp, precip data, etc.
    """
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
        self.bw = Bewdy(self.control, self.params, self.state, self.fluxes,
                        self.met_data)
        self.wb = WaterBalance(self.control, self.params, self.state,
                               self.fluxes, self.met_data)
        
        self.mt = Mate(self.control, self.params, self.state, self.fluxes,
                       self.met_data)
        
        self.sm = SoilMoisture(self.control, self.params, self.state, 
                               self.fluxes)
        
        self.rm = RootingDepthModel(d0x=self.params.d0x, r0=self.params.r0, 
                                    top_soil_depth=self.params.top_soil_depth)
        
        # Window size = root lifespan in days...
        self.window_size = (int((self.params.rdecay * const.NDAYS_IN_YR) * 
                            const.NDAYS_IN_YR))
        self.sma = Simplemovingaverage(self.window_size)
        
        
    def calc_day_growth(self, project_day, fdecay, rdecay, daylen, doy, 
                        days_in_yr, yr_index):
        """Evolve plant state, photosynthesis, distribute N and C"

        Parameters:
        -----------
        project_day : integer
            simulation day
        fdecay : float
            foliage decay rate
        rdecay : float
            fine root decay rate
        """
        # calculate NPP
        self.carbon_production(project_day, daylen)

        # calculate water balance
        self.wb.calculate_water_balance(project_day, daylen)
        
        # leaf N:C as a fraction of Ncmaxyoung, i.e. the max N:C ratio of
        # foliage in young stand
        nitfac = min(1.0, self.state.shootnc / self.params.ncmaxfyoung)
        
        # figure out the C allocation fractions 
        self.calc_carbon_allocation_fracs(nitfac, yr_index)
        
        # Distribute new C and N through the system
        self.carbon_allocation(nitfac, doy, days_in_yr)
        
        (ncbnew, ncwimm, ncwnew) = self.calculate_ncwood_ratios(nitfac)
        self.nitrogen_allocation(ncbnew, ncwimm, ncwnew, fdecay, rdecay, doy,
                                 days_in_yr)
        
        self.update_plant_state(fdecay, rdecay, project_day, doy)
        if self.control.deciduous_model:
            self.precision_control()
        
    def calculate_ncwood_ratios(self, nitfac):
        """ Estimate the N:C ratio in the branch and stem. Option to vary
        the N:C ratio of the stem following Jeffreys (1999) or keep it a fixed
        fraction

        Parameters:
        -----------
        nitfac : float
            leaf N:C as a fraction of the max N:C ratio of foliage in young
            stand

        Returns:
        --------
        ncbnew : float
            N:C ratio of branch
        ncwimm : float
            N:C ratio of immobile stem
        ncwnew : float
            N:C ratio of mobile stem

        References:
        ----------
        * Jeffreys, M. P. (1999) Dynamics of stemwood nitrogen in Pinus radiata
          with modelled implications for forest productivity under elevated
          atmospheric carbon dioxide. PhD.
        """
        # n:c ratio of new branch wood
        ncbnew = (self.params.ncbnew + nitfac *
                 (self.params.ncbnew - self.params.ncbnewz))
        self.state.branchnc = ncbnew
        
        # fixed N:C in the stemwood
        if self.control.fixed_stem_nc == 1:
            # n:c ratio of stemwood - immobile pool and new ring
            ncwimm = (self.params.ncwimm + nitfac *
                     (self.params.ncwimm - self.params.ncwimmz))
            
            # New stem ring N:C at critical leaf N:C (mobile)
            ncwnew = (self.params.ncwnew + nitfac *
                     (self.params.ncwnew - self.params.ncwnewz))
            
        # vary stem N:C based on reln with foliage, see Jeffreys. Jeffreys 1999
        # showed that N:C ratio of new wood increases with foliar N:C ratio,
        # modelled here based on evidence as a linear function.
        else:
            ncwimm = max(0.0, (0.0282 * self.state.shootnc + 0.000234) * 
                         self.params.fhw)

            # New stem ring N:C at critical leaf N:C (mobile)
            ncwnew = max(0.0, 0.162 * self.state.shootnc - 0.00143)
        
        return (ncbnew, ncwimm, ncwnew)

    def carbon_production(self, project_day, daylen):
        """ Calculate GPP, NPP and plant respiration

        Parameters:
        -----------
        project_day : integer
            simulation day
        daylen : float
            daytime length (hrs)

        References:
        -----------
        * Jackson, J. E. and Palmer, J. W. (1981) Annals of Botany, 47, 561-565.
        """

        if self.state.lai > 0.0:
            # average leaf nitrogen content (g N m-2 leaf)
            leafn = (self.state.shootnc * self.params.cfracts /
                     self.state.sla * const.KG_AS_G)
            
            # total nitrogen content of the canopy
            self.state.ncontent = leafn * self.state.lai
        else:
            self.state.ncontent = 0.0
         
        # fractional ground cover.
        if float_lt(self.state.lai, self.params.lai_cover):
            frac_gcover = self.state.lai / self.params.lai_cover
        else:
            frac_gcover = 1.0

        # Radiance intercepted by the canopy, accounting for partial closure
        # Jackson and Palmer (1981), derived from beer's law
        if self.state.lai > 0.0:
            self.state.light_interception = ((1.0 - exp(-self.params.kext *
                                             self.state.lai / frac_gcover)) *
                                             frac_gcover)
        else:
            self.state.light_interception = 0.0
        
        if self.control.water_stress:
            # Calculate the soil moisture availability factors [0,1] in the 
            # topsoil and the entire root zone
            (self.state.wtfac_tsoil, 
             self.state.wtfac_root) = self.sm.calculate_soil_water_fac()
        else:
            # really this should only be a debugging option!
            self.state.wtfac_tsoil = 1.0
            self.state.wtfac_root = 1.0
       
        # Estimate photosynthesis 
        if self.control.assim_model == "BEWDY":
            self.bw.calculate_photosynthesis(frac_gcover, project_day, daylen)
        elif self.control.assim_model == "MATE":
            self.mt.calculate_photosynthesis(project_day, daylen)
        else:
            raise AttributeError('Unknown assimilation model')
    
    def calc_carbon_allocation_fracs(self, nitfac, yr_index):
        """Carbon allocation fractions to move photosynthate through the plant.

        Parameters:
        -----------
        nitfac : float
            leaf N:C as a fraction of 'Ncmaxfyoung' (max 1.0)

        Returns:
        --------
        alleaf : float
            allocation fraction for shoot
        alroot : float
            allocation fraction for fine roots
        albranch : float
            allocation fraction for branches
        alstem : float
            allocation fraction for stem
       
        References:
        -----------
        McMurtrie, R. E. et al (2000) Plant and Soil, 224, 135-152.
        """
        """
        if type(self.params.callocr) == type(list()):
            ar = self.params.callocr[yr_index]
            arz = self.params.callocrz[yr_index]
        else:
            ar = self.params.callocr
            arz = self.params.callocrz
        
        self.state.alleaf = (self.params.callocf + nitfac *
                            (self.params.callocf - self.params.callocfz))
          
        self.state.alroot = ar + nitfac * (ar - arz)

        self.state.albranch = (self.params.callocb + nitfac *
                              (self.params.callocb - self.params.callocbz))
        
        # allocate remainder to stem
        self.state.alstem = (1.0 - self.state.alleaf - self.state.alroot - 
                             self.state.albranch)
        
        #print self.state.alleaf, self.state.alroot, self.state.albranch, self.state.alstem
        
        """
        if self.control.alloc_model == "FIXED":
        
            self.state.alleaf = (self.params.callocf + nitfac *
                                (self.params.callocf - self.params.callocfz))
          
            self.state.alroot = (self.params.callocr + nitfac *
                                (self.params.callocr - self.params.callocrz))

            self.state.albranch = (self.params.callocb + nitfac *
                                  (self.params.callocb - self.params.callocbz))
        
            # allocate remainder to stem
            self.state.alstem = (1.0 - self.state.alleaf - self.state.alroot - 
                                 self.state.albranch)
        
        elif self.control.alloc_model == "ALLOMETRIC":
            
            # leaf N availability
            nf = self.state.shootnc
            if nf <= self.params.nf_min:
                nlim = 0.0
            elif self.params.nf_min < nf and nf < self.params.nf_max:
                nlim = ((self.params.nf_max - nf) / 
                        (self.params.nf_max - self.params.nf_min))
            elif nf >= self.params.nf_max:
                nlim = 1.0
        
            # need to have stored the first 300 ish days (depends on root 
            # lifespan) in order to calculate running mean
            if project_day > self.window_size:
                # limitation is the miniumum of the soil water availability and
                # leaf N availability.
                limitation = self.sma(min(nlim, self.state.wtfac_root))
            else:
                limitation = 1.0
        
            # figure out root allocation given available water & nutrients
            self.state.alroot = (self.params.ar_max * self.params.ar_min / 
                                (self.params.ar_min + 
                                (self.params.ar_max - self.params.ar_min) * 
                                limitation))
        
            # Calculate tree height: allometric reln using the power function 
            # (Causton, 1985)
            height = self.params.heighto * self.state.stem**self.params.htpower
        
            # LAI to stem sapwood cross-sectional area (As m-2 m-2) 
            # (dimensionless)
            # Assume it varies between LS0 and LS1 as a linear function of tree
            # height (m) 
            sap_cross_sec_area = (((self.state.sapwood * 
                                    const.TONNES_AS_KG * 
                                    const.M2_AS_HA) / 
                                    self.params.cfracts) / 
                                    height / 
                                    self.params.density)
            leaf2sap = self.state.lai / sap_cross_sec_area
        
            # Allocation to leaves dependant on height. Modification of pipe 
            # theory, leaf-to-sapwood ratio is not constant above a certain 
            # height, due to hydraulic constraints.
            if self.params.leafsap0 < self.params.leafsap1:
                min_target = self.params.leafsap0
            else:
                min_target = self.params.leafsap1
            
            if self.params.leafsap0 > self.params.leafsap1:
                max_target = self.params.leafsap0
            else:
                max_target = self.params.leafsap1
          
            leaf2sa_target = (self.params.leafsap0 + 
                             (self.params.leafsap1 - self.params.leafsap0) * 
                             (height - self.params.height0) / 
                             (self.params.height1 - self.params.height0))
            leaf2sa_target = clip(leaf2sa_target, min=min_target, max=max_target)
        
            self.state.alleaf = self.alloc_goal_seek(leaf2sap, leaf2sa_target, 
                                                     self.params.af_max, 
                                                     self.params.targ_sens) 
            
            # Allocation to branch dependent on relationship between the stem
            # and branch
            target_branch = (self.params.branch0 * 
                             self.state.stem**self.params.branch1)
            self.state.albranch = self.alloc_goal_seek(self.state.branch, 
                                                       target_branch, 
                                                       self.params.ab_max, 
                                                       self.params.targ_sens) 
            
            # allocation to stem is the residual
            self.state.alstem = (1.0 - self.state.alroot - 
                                       self.state.albranch - 
                                       self.state.alleaf)
        else:
            raise AttributeError('Unknown C allocation model')
        
        # Total allocation should be one, if not print warning:
        total_alloc = (self.state.alroot + self.state.alleaf + 
                       self.state.albranch + self.state.alstem)
        if float_gt(total_alloc, 1.0):
            raise RuntimeError, "Allocation fracs > 1" 
        
         
    def allocate_stored_c_and_n(self, init):
        """
        Allocate stored C&N. This is either down as the model is initialised 
        for the first time or at the end of each year. 
        """
        # JUST here for FACE stuff as first year of ele should have last years alloc fracs
        #if init == True:
        #    self.state.alleaf = 0.26
        #    self.state.alroot = 0.11
        #    self.state.albranch = 0.06
        #    self.state.alstem = 0.57
        
        # ========================
        # Carbon - fixed fractions
        # ========================
        self.state.c_to_alloc_shoot = self.state.alleaf * self.state.cstore
        self.state.c_to_alloc_root = self.state.alroot * self.state.cstore
        self.state.c_to_alloc_branch = self.state.albranch * self.state.cstore
        self.state.c_to_alloc_stem = self.state.alstem * self.state.cstore
        
        # =========
        # Nitrogen
        # =========
        
        # Fixed ratios N allocation to woody components.
        
        # N flux into new ring (immobile component -> structrual components)
        self.state.n_to_alloc_stemimm = (self.state.cstore * self.state.alstem * 
                                         self.params.ncwimm)
    
        # N flux into new ring (mobile component -> can be retrans for new
        # woody tissue)
        self.state.n_to_alloc_stemmob = (self.state.cstore * self.state.alstem * 
                                        (self.params.ncwnew - 
                                         self.params.ncwimm))
        
        self.state.n_to_alloc_branch = (self.state.cstore * 
                                        self.state.albranch * 
                                        self.params.ncbnew)
        
        # Calculate remaining N left to allocate to leaves and roots 
        ntot = (self.state.nstore - self.state.n_to_alloc_stemimm -
                self.state.n_to_alloc_stemmob - self.state.n_to_alloc_branch)
        
        # allocate remaining N to flexible-ratio pools
        self.state.n_to_alloc_shoot = (ntot * self.state.alleaf / 
                                      (self.state.alleaf + 
                                       self.state.alroot *
                                       self.params.ncrfac))
        self.state.n_to_alloc_root = ntot - self.state.n_to_alloc_shoot
        
        
    def nitrogen_allocation(self, ncbnew, ncwimm, ncwnew, fdecay, rdecay, doy,
                            days_in_yr):
        """ Nitrogen distribution - allocate available N through system.
        N is first allocated to the woody component, surplus N is then allocated
        to the shoot and roots with flexible ratios.
        
        References:
        -----------
        McMurtrie, R. E. et al (2000) Plant and Soil, 224, 135-152.
        
        Parameters:
        -----------
        ncbnew : float
            N:C ratio of branch
        ncwimm : float
            N:C ratio of immobile stem
        ncwnew : float
            N:C ratio of mobile stem
        fdecay : float
            foliage decay rate
        rdecay : float
            fine root decay rate
        """
        # N retranslocated proportion from dying plant tissue and stored within
        # the plant
        self.fluxes.retrans = self.nitrogen_retrans(fdecay, rdecay, doy)
        self.fluxes.nuptake = self.calculate_nuptake()
        
        # Ross's Root Model.
        if self.control.model_optroot == True:    
            
            # convert t ha-1 day-1 to gN m-2 year-1
            nsupply = (self.calculate_nuptake() * const.TONNES_HA_2_G_M2 * 
                       const.DAYS_IN_YRS)
            
            # covnert t ha-1 to kg DM m-2
            rtot = (self.state.root * const.TONNES_HA_2_KG_M2 / 
                    self.params.cfracts)
            
            (self.state.root_depth, 
             self.fluxes.nuptake,
             self.fluxes.rabove) = self.rm.main(rtot, nsupply, depth_guess=1.0)
            
            #umax = self.rm.calc_umax(self.fluxes.nuptake)
            #print umax
            
            # covert nuptake from gN m-2 year-1  to t ha-1 day-1
            self.fluxes.nuptake = (self.fluxes.nuptake * 
                                   const.G_M2_2_TONNES_HA * const.YRS_IN_DAYS)
            
            # covert from kg DM N m-2 to t ha-1
            self.fluxes.deadroots = (self.params.rdecay * self.fluxes.rabove * 
                                     self.params.cfracts * 
                                     const.KG_M2_2_TONNES_HA)
            
            self.fluxes.deadrootn = (self.state.rootnc * 
                                    (1.0 - self.params.rretrans) * 
                                     self.fluxes.deadroots)
            
           
        # Mineralised nitrogen lost from the system by volatilisation/leaching
        self.fluxes.nloss = self.params.rateloss * self.state.inorgn
    
        # total nitrogen to allocate 
        ntot = self.fluxes.nuptake + self.fluxes.retrans
        
        if self.control.deciduous_model:
            # allocate N to pools with fixed N:C ratios
            
            # N flux into new ring (immobile component -> structrual components)
            self.fluxes.npstemimm = (self.fluxes.wnimrate * 
                                     self.state.growing_days[doy])
            
            # N flux into new ring (mobile component -> can be retrans for new
            # woody tissue)
            self.fluxes.npstemmob = (self.fluxes.wnmobrate * 
                                     self.state.growing_days[doy])
            
            self.fluxes.nproot = self.state.n_to_alloc_root / days_in_yr
            
            self.fluxes.npleaf = (self.fluxes.lnrate * 
                                  self.state.growing_days[doy])
            
            self.fluxes.npbranch = (self.fluxes.bnrate * 
                                    self.state.growing_days[doy])
        else:
            # allocate N to pools with fixed N:C ratios
            
            # N flux into new ring (immobile component -> structural components)
            self.fluxes.npstemimm = self.fluxes.npp * self.state.alstem * ncwimm
    
            # N flux into new ring (mobile component -> can be retrans for new
            # woody tissue)
            self.fluxes.npstemmob = (self.fluxes.npp * self.state.alstem * 
                                     (ncwnew - ncwimm))
            self.fluxes.npbranch = (self.fluxes.npp * self.state.albranch * 
                                     ncbnew)
            
            # If we have allocated more N than we have available 
            #  - cut back N prodn
            arg = (self.fluxes.npstemimm + self.fluxes.npstemmob +
                   self.fluxes.npbranch )
    
            if float_gt(arg, ntot) and self.control.fixleafnc == False:
                self.fluxes.npp *= (ntot / (self.fluxes.npstemimm +
                                    self.fluxes.npstemmob + 
                                    self.fluxes.npbranch ))
                self.fluxes.npbranch = (self.fluxes.npp * self.state.albranch * 
                                        ncbnew)
                self.fluxes.npstemimm = (self.fluxes.npp * self.state.alstem * 
                                         ncwimm)
                self.fluxes.npstemmob = (self.fluxes.npp * self.state.alstem * 
                                        (ncwnew - ncwimm))
                
                
            ntot -= (self.fluxes.npbranch + self.fluxes.npstemimm +
                        self.fluxes.npstemmob)
            
            # allocate remaining N to flexible-ratio pools
            self.fluxes.npleaf = (ntot * self.state.alleaf / 
                                 (self.state.alleaf + self.state.alroot *
                                 self.params.ncrfac))
            self.fluxes.nproot = ntot - self.fluxes.npleaf
        
        
    def nitrogen_retrans(self, fdecay, rdecay, doy):
        """ Nitrogen retranslocated from senesced plant matter.
        Constant rate of n translocated from mobile pool

        Parameters:
        -----------
        fdecay : float
            foliage decay rate
        rdecay : float
            fine root decay rate

        Returns:
        --------
        N retrans : float
            N retranslocated plant matter

        """
        if self.control.deciduous_model:
            leafretransn = (self.params.fretrans * self.fluxes.lnrate * 
                            self.state.remaining_days[doy])
        else:
            leafretransn = self.params.fretrans * fdecay * self.state.shootn
        
        arg1 = (leafretransn +
                self.params.rretrans * rdecay * self.state.rootn +
                self.params.bretrans * self.params.bdecay *
                self.state.branchn)
        arg2 = (self.params.wretrans * self.params.wdecay *
                self.state.stemnmob + self.params.retransmob *
                self.state.stemnmob)
        
        return arg1 + arg2
    
    def calculate_nuptake(self):
        """ N uptake from the soil, note as it stands root biomass does not
        affect N uptake.
        
        Returns:
        --------
        nuptake : float
            N uptake
            
        References:
        -----------
        * Dewar and McMurtrie, 1996, Tree Physiology, 16, 161-171.    
            
        """
        if self.control.nuptake_model == 0:
            # Constant N uptake
            nuptake = self.params.nuptakez
        elif self.control.nuptake_model == 1:
            # evaluate nuptake : proportional to dynamic inorganic N pool
            nuptake = self.params.rateuptake * self.state.inorgn
        elif self.control.nuptake_model == 2:
            # Assume N uptake depends on the rate at which soil mineral
            # N is made available (self.params.Uo) and the value or root C
            # at which 50% of the available N is taken up (Dewar and McM).
            arg = (self.params.uo * self.state.inorgn *
                    (self.state.root / (self.state.root + self.params.kr)))
            nuptake = max(arg, 0.0)
        else:
            raise AttributeError('Unknown N uptake assumption')
        
        return nuptake
    
    def carbon_allocation(self, nitfac, doy, days_in_yr):
        """ C distribution - allocate available C through system

        Parameters:
        -----------
        nitfac : float
            leaf N:C as a fraction of 'Ncmaxfyoung' (max 1.0)
        """
        if self.control.deciduous_model:
            days_left = self.state.growing_days[doy]
            self.fluxes.cpleaf = self.fluxes.lrate * days_left
            self.fluxes.cpbranch = self.fluxes.brate * days_left
            self.fluxes.cpstem = self.fluxes.wrate * days_left
            self.fluxes.cproot = self.state.c_to_alloc_root * 1.0 / days_in_yr
        else:
            self.fluxes.cpleaf = self.fluxes.npp * self.state.alleaf
            self.fluxes.cproot = self.fluxes.npp * self.state.alroot
            self.fluxes.cpbranch = self.fluxes.npp * self.state.albranch
            self.fluxes.cpstem = self.fluxes.npp * self.state.alstem
        
        # evaluate SLA of new foliage accounting for variation in SLA 
        # with tree and leaf age (Sands and Landsberg, 2002). Assume 
        # SLA of new foliage is linearly related to leaf N:C ratio 
        # via nitfac. Based on date from two E.globulus stands in SW Aus, see
        # Corbeels et al (2005) Ecological Modelling, 187, 449-474.
        # (m2 onesided/kg DW)
        self.state.sla = (self.params.slazero + nitfac *
                         (self.params.slamax - self.params.slazero))
        
        if self.control.deciduous_model:
            if float_eq(self.state.shoot, 0.0):
                self.state.lai = 0.0
            elif self.state.leaf_out_days[doy] > 0.0:               
                self.state.lai += (self.fluxes.cpleaf * 
                                  (self.state.sla * const.M2_AS_HA / 
                                  (const.KG_AS_TONNES * self.params.cfracts)) -
                                  (self.fluxes.deadleaves + 
                                   self.fluxes.ceaten) *
                                   self.state.lai / self.state.shoot)
            else:
                self.state.lai = 0.0
        else:
            # update leaf area [m2 m-2]
            self.state.lai += (self.fluxes.cpleaf * 
                              (self.state.sla * const.M2_AS_HA / 
                              (const.KG_AS_TONNES * self.params.cfracts)) -
                              (self.fluxes.deadleaves + 
                               self.fluxes.ceaten) *
                               self.state.lai / self.state.shoot)
   
    def precision_control(self, tolerance=1E-08):
        """ Detect very low values in state variables and force to zero to 
        avoid rounding and overflow errors """       
        
        # C & N state variables 
        if self.state.shoot < tolerance:
            self.fluxes.deadleaves += self.state.shoot
            self.fluxes.deadleafn += self.state.shootn
            self.state.shoot = 0.0 
            self.state.shootn = 0.0 
            
        if self.state.branch < tolerance:
            self.fluxes.deadbranch += self.state.branch
            self.fluxes.deadbranchn += self.state.branchn
            self.state.branch = 0.0
            self.state.branchn = 0.0

        if self.state.root < tolerance:
            self.fluxes.deadrootn += self.state.rootn
            self.fluxes.deadroots += self.state.root
            self.state.root = 0.0
            self.state.rootn = 0.0
    
        if self.state.stem < tolerance:     
            self.fluxes.deadstemn += self.state.stem
            self.state.stem = 0.0
            self.state.stemnimm = 0.0
            self.state.stemnmob = 0.0
            
        # should add check for soil pools - excess goes where?
        
    def update_plant_state(self, fdecay, rdecay, project_day, doy):
        """ Daily change in C content

        Parameters:
        -----------
        fdecay : float
            foliage decay rate
        rdecay : float
            fine root decay rate

        """
        # 
        # Carbon pools
        #
        self.state.shoot += (self.fluxes.cpleaf - self.fluxes.deadleaves -
                             self.fluxes.ceaten)
        self.state.root += self.fluxes.cproot - self.fluxes.deadroots
        self.state.branch += self.fluxes.cpbranch - self.fluxes.deadbranch
        self.state.stem += self.fluxes.cpstem - self.fluxes.deadstems
        self.state.sapwood += self.fluxes.cpstem - self.fluxes.deadsapwood
        # 
        # Nitrogen pools
        #
        if self.control.deciduous_model:       
            self.state.shootn += (self.fluxes.npleaf - 
                                 (self.fluxes.lnrate * 
                                  self.state.remaining_days[doy]) - 
                                  self.fluxes.neaten)                        
        else:
            self.state.shootn += (self.fluxes.npleaf - 
                                  fdecay * self.state.shootn - 
                                  self.fluxes.neaten)
                                
        self.state.branchn += (self.fluxes.npbranch - self.params.bdecay *
                               self.state.branchn)
        self.state.rootn += self.fluxes.nproot - rdecay * self.state.rootn
        
        self.state.stemnimm += (self.fluxes.npstemimm - self.params.wdecay *
                                self.state.stemnimm)
        self.state.stemnmob += (self.fluxes.npstemmob - self.params.wdecay *
                                self.state.stemnmob -
                                self.params.retransmob * self.state.stemnmob)
        self.state.stemn = self.state.stemnimm + self.state.stemnmob

        if self.control.deciduous_model:
            self.calculate_cn_store()
        
        #============================
        # Enforce maximum N:C ratios.
        # ===========================    
        # This doesn't make sense for the deciduous model because of the ramp
        # function. The way the deciduous logic works we now before we start
        # how much N we have to allocate so it is impossible to allocate in 
        # excess. Therefore this is only relevant for evergreen model.
        if not self.control.deciduous_model:
            
            # If foliage or root N/C exceeds its max, then N uptake is cut back
            
            # maximum leaf n:c ratio is function of stand age
            #  - switch off age effect by setting ncmaxfyoung = ncmaxfold
            age_effect = ((self.state.age - self.params.ageyoung) / 
                          (self.params.ageold - self.params.ageyoung))

            ncmaxf = (self.params.ncmaxfyoung - 
                     (self.params.ncmaxfyoung - self.params.ncmaxfold) * 
                      age_effect)
    
            if float_lt(ncmaxf, self.params.ncmaxfold):
                ncmaxf = self.params.ncmaxfold

            if float_gt(ncmaxf, self.params.ncmaxfyoung):
                ncmaxf = self.params.ncmaxfyoung
    
            extras = 0.0
            if self.state.lai > 0.0:

                if float_gt(self.state.shootn, (self.state.shoot * ncmaxf)):
                    extras = self.state.shootn - self.state.shoot * ncmaxf

                    # Ensure N uptake cannot be reduced below zero.
                    if float_gt(extras, self.fluxes.nuptake):
                        extras = self.fluxes.nuptake

                    self.state.shootn -= extras
                    self.fluxes.nuptake -= extras
                    
            # if root N:C ratio exceeds its max, then nitrogen uptake is cut 
            # back. n.b. new ring n/c max is already set because it is related 
            # to leaf n:c
            ncmaxr = ncmaxf * self.params.ncrfac  # max root n:c
            extrar = 0.0
            if float_gt(self.state.rootn, (self.state.root * ncmaxr)):
       
                extrar = self.state.rootn - self.state.root * ncmaxr

                # Ensure N uptake cannot be reduced below zero.
                if float_gt((extras + extrar), self.fluxes.nuptake):
                    extrar = self.fluxes.nuptake - extras

                self.state.rootn -= extrar
                self.fluxes.nuptake -= extrar 
                
    def calculate_cn_store(self):        
        
        # Total C & N storage to allocate annually.
        self.state.cstore += self.fluxes.npp
        self.state.nstore += self.fluxes.nuptake + self.fluxes.retrans 
        self.state.anpp += self.fluxes.npp
  
    def calc_microbial_resp(self, project_day):
        """ Based on LPJ-why
        
        References:
        * Wania (2009) Integrating peatlands and permafrost into a dynamic 
          global vegetation model: 1. Evaluation and sensitivity of physical 
          land surface processes. GBC, 23, GB3014.
        * Also part 2 and the geosci paper in 2010
        """
        tsoil = self.met_data['tsoil'][project_day]
        
        # Lloyd and Taylor, 1994
        if tsoil < -10.0:
            temp_resp = 0.0
        else:
            temp_resp = (exp(308.56 * ((1.0 / 56.02) - (1.0 / 
                        (tsoil + const.DEG_TO_KELVIN - 227.13)))))
        
        moist_resp = ((1.0 - exp(-1.0 * self.state.wtfac_tsoil)) /  
                        (1.0 - exp(-1.0)))
        
        # Pool turnover rate = every 2 weeks -> days. Check you have this right
        # and turn into a parameter if so
        k_exu10 = 0.0714128571 
        k_exu = k_exu10 * temp_resp * moist_resp
        
        return  self.state.exu_pool * (1.0 - exp(-k_exu))

  
        
if __name__ == "__main__":
    
    # timing...
    import sys
    import time
    start_time = time.time()
    
    from file_parser import initialise_model_data
    from utilities import float_lt, day_length
    import datetime

    fname = "/Users/mdekauwe/src/python/pygday/params/duke_testing.cfg"

    (control, params, state, files,
        fluxes, met_data,
            print_opts) = initialise_model_data(fname, DUMP=False)

    # figure out photosynthesis
    PG = PlantGrowth(control, params, state, fluxes, met_data)

    state.lai = (params.slainit * const.M2_AS_HA /
                            const.KG_AS_TONNES / params.cfracts *
                            state.shoot)

    # Specific LAI (m2 onesided/kg DW)
    state.sla = params.slainit


    year = str(control.startyear)
    month = str(control.startmonth)
    day = str(control.startday)
    datex = datetime.datetime.strptime((year + month + day), "%Y%m%d")

    #laifname = "/Users/mdekauwe/research/NCEAS_face/GDAY_duke_simulation/experiments/lai"
    #import numpy as np
    #laidata = np.loadtxt(laifname)

    fdecay = 0.5
    rdecay = 0.5
    fluxes.deadleaves = 0.0
    fluxes.ceaten = 0.0
    fluxes.neaten = 0.0
    fluxes.deadroots = 0.0
    fluxes.deadbranch = 0.0         
    fluxes.deadstems = 0.0
    for project_day in xrange(len(met_data['prjday'])):

        state.shootnc = state.shootn / state.shoot
        state.ncontent = (state.shootnc * params.cfracts /
                                state.sla * const.KG_AS_G)
        daylen = day_length(datex, params.latitude)
        state.wtfac_root = 1.0
        #state.lai = laidata[project_day]


        if float_lt(state.lai, params.lai_cover):
            frac_gcover = state.lai / params.lai_cover
        else:
            frac_gcover = 1.0

        state.light_interception = ((1.0 - exp(-params.kext *
                                            state.lai / frac_gcover)) *
                                            frac_gcover)



        PG.grow(project_day, datex, fdecay, rdecay)
        print fluxes.gpp / const.HA_AS_M2 * const.TONNES_AS_G



        datex += datetime.timedelta(days=1)
    end_time = time.time()
    sys.stderr.write("\nTotal simulation time: %.1f seconds\n\n" %
                                                    (end_time - start_time))
    
    