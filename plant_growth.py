""" Estimate daily Carbon fixed and pass around the aboveground portion of the
plant. """
import sys
from math import exp, log
import sys
import constants as const
from utilities import float_eq, float_lt, float_gt, SimpleMovingAverage, clip
from utilities import float_le, float_ge
from bewdy import Bewdy
from water_balance import WaterBalance, SoilMoisture
from mate import MateC3, MateC4
from optimal_root_model import RootingDepthModel

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
        
        
        if self.control.ps_pathway == "C3":
            self.mt = MateC3(self.control, self.params, self.state, self.fluxes,
                             self.met_data)
        else:
            self.mt = MateC4(self.control, self.params, self.state, self.fluxes,
                             self.met_data)
                             
        self.sm = SoilMoisture(self.control, self.params, self.state, 
                               self.fluxes)
        self.sm.initialise_parameters()
        
        self.rm = RootingDepthModel(d0x=self.params.d0x, r0=self.params.r0, 
                                    top_soil_depth=self.params.topsoil_depth*const.MM_TO_M)
        
        # Window size = root lifespan in days...
        self.window_size = (int(1.0 / (self.params.rdecay * const.NDAYS_IN_YR)* 
                            const.NDAYS_IN_YR))
        #self.window_size = 365
        
        # If we don't have any information about the N&water limitation, i.e.
        # as would be the case with spin-up, assume that there is no limitation
        # to begin with.
        if self.state.prev_sma is None:
            self.state.prev_sma = 1.0 
        if self.state.grw_seas_stress is None:
            self.state.grw_seas_stress = 1.0
        
        self.sma = SimpleMovingAverage(self.window_size, self.state.prev_sma)
        
        
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
        # if grazing took place need to reset "stress" running mean calculation
        # for grasses
        if self.control.grazing == 2 and self.params.disturbance_doy == doy: 
            self.sma.reset_stream()
        
        # calculate NPP
        self.carbon_production(project_day, daylen)

        # calculate water balance. We also need to store the previous days
        # soil water store
        previous_topsoil_store = self.state.pawater_topsoil
        previous_rootzone_store = self.state.pawater_root
        self.wb.calculate_water_balance(project_day, daylen)
        
        # leaf N:C as a fraction of Ncmaxyoung, i.e. the max N:C ratio of
        # foliage in young stand
        nitfac = min(1.0, self.state.shootnc / self.params.ncmaxfyoung)
        
        # figure out the C allocation fractions 
        if not self.control.deciduous_model:
            # daily allocation...
            self.calc_carbon_allocation_fracs(nitfac)
        else:
            # Allocation is annually for deciduous "tree" model, but we need to 
            # keep a check on stresses during the growing season and the LAI
            # figure out limitations during leaf growth period. This also
            # applies for deciduous grasses, need to do the growth stress
            # calc for grasses here too.
            if self.state.leaf_out_days[doy] > 0.0:
                self.calculate_growth_stress_limitation()
                
                # Need to save max lai for pipe model because at the end of the
                # year LAI=0.0
                if self.state.lai > self.state.max_lai:
                    self.state.max_lai = self.state.lai
        
        
        
                   
        # Distribute new C and N through the system
        self.carbon_allocation(nitfac, doy, days_in_yr)
        
        (ncbnew, nccnew, ncwimm, ncwnew) = self.calculate_ncwood_ratios(nitfac)
        recalc_wb = self.nitrogen_allocation(ncbnew, nccnew, ncwimm, ncwnew, fdecay, 
                                             rdecay, doy, days_in_yr, 
                                             project_day)
        
        if self.control.exudation:
            self.calc_root_exudation_release()
        
        # If we didn't have enough N available to satisfy wood demand, NPP
        # is down-regulated and thus so is GPP. We also need to recalculate the
        # water balance given the lower GPP.
        if recalc_wb:
            self.state.pawater_topsoil = previous_topsoil_store 
            self.state.pawater_root = previous_rootzone_store
            self.wb.calculate_water_balance(project_day, daylen)
            
        self.update_plant_state(fdecay, rdecay, project_day, doy)
        #if self.control.deciduous_model:
        
        self.precision_control()
        
    def calc_root_exudation_release(self):
        """
        Root exudation can be modeled to occur: 
            1) simultaneously with root growth
            2) as a result of excess C. 
        """
        leaf_CN = 1.0 / self.state.shootnc
        presc_leaf_CN = 30.0 # make a parameter.
        
        # fraction varies between 0 and 50 % as a function of leaf CN
        frac_to_rexc = max(0.0, min(0.5, (leaf_CN / presc_leaf_CN) - 1.0))

        self.fluxes.root_exc = frac_to_rexc * self.fluxes.cproot
        self.fluxes.root_exn = self.fluxes.root_exc / self.state.rootnc
        
        # Need to remove lost C & N from fine roots so that things balance.
        self.fluxes.cproot -= self.fluxes.root_exc
        self.fluxes.nproot -= self.fluxes.root_exn

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
        
        # n:c ratio of new coarse root 
        nccnew = (self.params.nccnew + nitfac *
                 (self.params.nccnew - self.params.nccnewz))
        
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
        
        return (ncbnew, nccnew, ncwimm, ncwnew)

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
                     self.params.sla * const.KG_AS_G)
            
            # total nitrogen content of the canopy
            self.state.ncontent = leafn * self.state.lai
        else:
            self.state.ncontent = 0.0
         
        # When canopy is not closed, canopy light interception is reduced
        cf = min(1.0, self.state.lai / self.params.lai_cover)
        
        # fIPAR - the fraction of intercepted PAR = IPAR/PAR incident at the 
        # top of the canopy, accounting for partial closure based on Jackson
        # and Palmer (1981), derived from beer's law
        if self.state.lai > 0.0:
            self.state.fipar = ((1.0 - exp(-self.params.kext * 
                                           self.state.lai / cf)) * cf)
        else:
            self.state.fipar = 0.0
        
        # Canopy extinction coefficient if the canopy is open
        #if cf < 1.0:
        #    kext = -log(1.0 - self.state.fipar) / LAI
        
        if self.control.water_stress:
            # Calculate the soil moisture availability factors [0,1] in the 
            # topsoil and the entire root zone
            (self.state.wtfac_topsoil, 
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
    
    def calc_carbon_allocation_fracs(self, nitfac):
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
        Corbeels, M. et al (2005) Ecological Modelling, 187, 449-474.
        McMurtrie, R. E. et al (2000) Plant and Soil, 224, 135-152.
        
        """
        if self.control.alloc_model == "FIXED":
        
            self.fluxes.alleaf = (self.params.c_alloc_fmax + nitfac *
                                 (self.params.c_alloc_fmax - 
                                 self.params.c_alloc_fmin))
            
            self.fluxes.alroot = (self.params.c_alloc_rmax + nitfac *
                                 (self.params.c_alloc_rmax - 
                                 self.params.c_alloc_rmin))

            self.fluxes.albranch = (self.params.c_alloc_bmax + nitfac *
                                   (self.params.c_alloc_bmax - 
                                   self.params.c_alloc_bmin))
        
            # allocate remainder to stem
            self.fluxes.alstem = (1.0 - self.fluxes.alleaf - 
                                  self.fluxes.alroot - 
                                  self.fluxes.albranch)
            
            self.fluxes.alcroot = self.params.c_alloc_cmax * self.fluxes.alstem
            self.fluxes.alstem -= self.fluxes.alcroot
            
        elif self.control.alloc_model == "GRASSES":
            
            # if combining grasses with the deciduous model this calculation
            # is done only during the leaf out period. See above.
            if not self.control.deciduous_model:
                self.calculate_growth_stress_limitation()
            
            # figure out root allocation given available water & nutrients
            # hyperbola shape to allocation
            min_root_alloc = 0.4
            self.fluxes.alroot = (self.params.c_alloc_rmax * 
                                  min_root_alloc / 
                                 (min_root_alloc + 
                                 (self.params.c_alloc_rmax - 
                                  min_root_alloc) * 
                                  self.state.prev_sma))
            
            self.fluxes.alstem = 0.0
            self.fluxes.albranch = 0.0
            self.fluxes.alcroot = 0.0
            self.fluxes.alleaf = (1.0 - self.fluxes.alroot)
            
        elif self.control.alloc_model == "ALLOMETRIC":
            
            if not self.control.deciduous_model:
                self.calculate_growth_stress_limitation()
            else:
                # reset the buffer at the end of the growing season
                self.sma.reset_stream()
                
            # figure out root allocation given available water & nutrients
            # hyperbola shape to allocation
            min_root_alloc = 0.1
            self.fluxes.alroot = (self.params.c_alloc_rmax * 
                                  min_root_alloc / 
                                 (min_root_alloc + 
                                 (self.params.c_alloc_rmax - 
                                  min_root_alloc) * 
                                  self.state.prev_sma))
            
            #self.fluxes.alroot = (self.params.c_alloc_rmin + 
            #                    (self.params.c_alloc_rmax - 
            #                     self.params.c_alloc_rmin) * 
            #                     self.state.prev_sma)
            
            
            # Calculate tree height: allometric reln using the power function 
            # (Causton, 1985)
            self.state.canht = (self.params.heighto * 
                                self.state.stem**self.params.htpower)

            # LAI to stem sapwood cross-sectional area (As m-2 m-2) 
            # (dimensionless)
            # Assume it varies between LS0 and LS1 as a linear function of tree
            # height (m) 
            arg1 = self.state.sapwood * const.TONNES_AS_KG * const.M2_AS_HA
            arg2 = self.state.canht * self.params.density * self.params.cfracts
            sap_cross_sec_area = arg1 / arg2
            
            if not self.control.deciduous_model:
                leaf2sap = self.state.lai / sap_cross_sec_area
            else:
                leaf2sap = self.state.max_lai / sap_cross_sec_area

            # Allocation to leaves dependant on height. Modification of pipe 
            # theory, leaf-to-sapwood ratio is not constant above a certain 
            # height, due to hydraulic constraints (Magnani et al 2000; Deckmyn
            # et al. 2006).
            
            if float_le(self.state.canht, self.params.height0):
                leaf2sa_target = self.params.leafsap0
            elif float_ge(self.state.canht, self.params.height1):
                leaf2sa_target = self.params.leafsap1
            else:
                arg1 = self.params.leafsap0
                arg2 = self.params.leafsap1 - self.params.leafsap0
                arg3 = self.state.canht - self.params.height0
                arg4 = self.params.height1 - self.params.height0
                leaf2sa_target = arg1 + (arg2 * arg3 / arg4) 
                
            self.fluxes.alleaf = self.alloc_goal_seek(leaf2sap, leaf2sa_target, 
                                                      self.params.c_alloc_fmax, 
                                                      self.params.targ_sens) 
            
            
            # Allocation to branch dependent on relationship between the stem
            # and branch
            target_branch = (self.params.branch0 * 
                             self.state.stem**self.params.branch1)
            self.fluxes.albranch = self.alloc_goal_seek(self.state.branch, 
                                                       target_branch, 
                                                       self.params.c_alloc_bmax, 
                                                       self.params.targ_sens) 
            
            coarse_root_target = (self.params.croot0 * 
                                  self.state.stem**self.params.croot1)
            self.fluxes.alcroot = self.alloc_goal_seek(self.state.croot, 
                                                       coarse_root_target, 
                                                       self.params.c_alloc_cmax, 
                                                       self.params.targ_sens) 
            
            self.fluxes.alstem = (1.0 - self.fluxes.alroot - 
                                        self.fluxes.albranch - 
                                        self.fluxes.alleaf -
                                        self.fluxes.alcroot)
            
            
            # allocation to stem is the residual
            #self.fluxes.alstem = (1.0 - self.fluxes.alroot - 
            #                            self.fluxes.albranch - 
            #                            self.fluxes.alleaf)
            #self.fluxes.alcroot = 0.2 * self.fluxes.alstem
            #self.fluxes.alstem -= self.fluxes.alcroot
            
            # Because I have allowed the max fracs sum > 1, possibility
            # stem frac would be negative. Perhaps the above shouldn't be 
            # allowed...? But this will stop wood allocation in such a 
            # situation.
            #if self.fluxes.alstem < 0.0:
            #    extra = self.fluxes.alstem
            #    self.fluxes.alstem = 0.0
            #    self.fluxes.alleaf -= extra
            
            # minimum allocation to leaves - without it tree would die, as this
            # is done annually.
            if self.control.deciduous_model:
                if self.fluxes.alleaf < 0.1:
                    min_leaf_alloc = 0.1
                    self.fluxes.alstem -= min_leaf_alloc
                    self.fluxes.alleaf = min_leaf_alloc
            
        else:
            raise AttributeError('Unknown C allocation model')
        
        #print self.fluxes.alleaf, self.fluxes.alstem, self.fluxes.albranch, \
        #       self.fluxes.alroot, self.state.prev_sma, self.state.canht
        
        
        
        # Total allocation should be one, if not print warning:
        total_alloc = (self.fluxes.alroot + self.fluxes.alleaf + 
                       self.fluxes.albranch + self.fluxes.alstem + 
                       self.fluxes.alcroot)
        if float_gt(total_alloc, 1.0):
            raise RuntimeError, "Allocation fracs > 1" 
        
    def alloc_goal_seek(self, simulated, target, alloc_max, sensitivity):
        
        # Sensitivity parameter characterises how allocation fraction respond 
        # when the leaf:sapwood area ratio departs from the target value 
        # If sensitivity close to 0 then the simulated leaf:sapwood area ratio 
        # will closely track the target value 
        frac = 0.5 + 0.5 * (1.0 - simulated / target) / sensitivity
        
        return max(0.0, alloc_max * min(1.0, frac))    
    
    
    def calculate_growth_stress_limitation(self):
        """ Calculate level of stress due to nitrogen or water availability """
        # calculate the N limitation based on available canopy N
        # this logic appears counter intuitive, but it works out when
        # applied with the perhaps backwards logic below
        nf = self.state.shootnc
    
        # case - completely limited by N availability
        if nf < self.params.nf_min:
            nlim = 0.0
        elif nf < self.params.nf_crit:
       
            nlim = ((nf - self.params.nf_min) / 
                    (self.params.nf_crit - self.params.nf_min))
        # case - no N limitation
        else:
            nlim = 1.0
        
        # Limitation by nitrogen and water. Water constraint is implicit, 
        # in that, water stress results in an increase of root mass,
        # which are assumed to spread horizontally within the rooting zone.
        # So in effect, building additional root mass doesnt alleviate the
        # water limitation within the model. However, it does more 
        # accurately reflect an increase in root C production at a water
        # limited site. This implementation is also consistent with other
        # approaches, e.g. LPJ. In fact I dont see much evidence for models
        # that have a flexible bucket depth.
        current_limitation = min(nlim, self.state.wtfac_root)
        self.state.prev_sma = self.sma(current_limitation)
        
        
    def allocate_stored_c_and_n(self, init):
        """
        Allocate stored C&N. This is either down as the model is initialised 
        for the first time or at the end of each year. 
        """
        # JUST here for FACE stuff as first year of ele should have last years 
        # alloc fracs
        #if init == True:
        #    self.fluxes.alleaf = 0.26
        #    self.fluxes.alroot = 0.11
        #    self.fluxes.albranch = 0.06
        #    self.fluxes.alstem = 0.57
                
        # ========================
        # Carbon - fixed fractions
        # ========================
        self.state.c_to_alloc_shoot = self.fluxes.alleaf * self.state.cstore
        self.state.c_to_alloc_root = self.fluxes.alroot * self.state.cstore
        self.state.c_to_alloc_croot = self.fluxes.alcroot * self.state.cstore
        self.state.c_to_alloc_branch = self.fluxes.albranch * self.state.cstore
        self.state.c_to_alloc_stem = self.fluxes.alstem * self.state.cstore
        
        
        # =========================================================
        # Nitrogen - Fixed ratios N allocation to woody components.
        # =========================================================
        
        # N flux into new ring (immobile component -> structrual components)
        self.state.n_to_alloc_stemimm = (self.state.cstore * 
                                         self.fluxes.alstem * 
                                         self.params.ncwimm)
    
        # N flux into new ring (mobile component -> can be retrans for new
        # woody tissue)
        self.state.n_to_alloc_stemmob = (self.state.cstore * 
                                         self.fluxes.alstem * 
                                        (self.params.ncwnew - 
                                         self.params.ncwimm))

        self.state.n_to_alloc_branch = (self.state.cstore * 
                                        self.fluxes.albranch * 
                                        self.params.ncbnew)
        
        self.state.n_to_alloc_croot = (self.state.cstore * 
                                        self.fluxes.alcroot * 
                                        self.params.nccnew)
                                        
        # Calculate remaining N left to allocate to leaves and roots 
        ntot = max(0.0,(self.state.nstore - self.state.n_to_alloc_stemimm -
                        self.state.n_to_alloc_stemmob - 
                        self.state.n_to_alloc_branch))
        
       
        # allocate remaining N to flexible-ratio pools
        self.state.n_to_alloc_shoot = (ntot * self.fluxes.alleaf / 
                                      (self.fluxes.alleaf + 
                                       self.fluxes.alroot *
                                       self.params.ncrfac))
        self.state.n_to_alloc_root = ntot - self.state.n_to_alloc_shoot
               
        
    def nitrogen_allocation(self, ncbnew, nccnew, ncwimm, ncwnew, fdecay, rdecay, doy,
                            days_in_yr, project_day):
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
        # default is we don't need to recalculate the water balance, 
        # however if we cut back on NPP due to available N below then we do
        # need to do this
        recalc_wb = False
        
        # N retranslocated proportion from dying plant tissue and stored within
        # the plant
        self.fluxes.retrans = self.nitrogen_retrans(fdecay, rdecay, doy)
        self.fluxes.nuptake = self.calculate_nuptake(project_day)
        
        # Ross's Root Model.
        if self.control.model_optroot == True:    
            
            # convert t ha-1 day-1 to gN m-2 year-1
            nsupply = (self.calculate_nuptake() * const.TONNES_HA_2_G_M2 * 
                       const.DAYS_IN_YRS)
            
            # covnert t ha-1 to kg DM m-2
            rtot = (self.state.root * const.TONNES_HA_2_KG_M2 / 
                    self.params.cfracts)
            self.fluxes.nuptake_old = self.fluxes.nuptake
            
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
        ntot = max(0.0, self.fluxes.nuptake + self.fluxes.retrans)
        
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
            self.fluxes.npcroot = (self.fluxes.cnrate * 
                                   self.state.growing_days[doy])
            
            self.fluxes.npleaf = (self.fluxes.lnrate * 
                                  self.state.growing_days[doy])
            
            self.fluxes.npbranch = (self.fluxes.bnrate * 
                                    self.state.growing_days[doy])
        else:
            # allocate N to pools with fixed N:C ratios
            
            # N flux into new ring (immobile component -> structural components)
            self.fluxes.npstemimm = self.fluxes.npp * self.fluxes.alstem * ncwimm
    
            # N flux into new ring (mobile component -> can be retrans for new
            # woody tissue)
            self.fluxes.npstemmob = (self.fluxes.npp * self.fluxes.alstem * 
                                     (ncwnew - ncwimm))
            self.fluxes.npbranch = (self.fluxes.npp * self.fluxes.albranch * 
                                     ncbnew)
            
            self.fluxes.npcroot = (self.fluxes.npp * self.fluxes.alcroot * 
                                     nccnew)
            
            # If we have allocated more N than we have available 
            #  - cut back N prodn
            arg = (self.fluxes.npstemimm + self.fluxes.npstemmob +
                   self.fluxes.npbranch + self.fluxes.npcroot)
            
            if float_gt(arg, ntot) and self.control.fixleafnc == False:
                
                self.fluxes.npp *= (ntot / (self.fluxes.npstemimm +
                                    self.fluxes.npstemmob + 
                                    self.fluxes.npbranch ))
                
                # need to adjust growth values accordingly as well
                self.fluxes.cpleaf = self.fluxes.npp * self.fluxes.alleaf
                self.fluxes.cproot = self.fluxes.npp * self.fluxes.alroot
                self.fluxes.cpcroot = self.fluxes.npp * self.fluxes.alcroot
                self.fluxes.cpbranch = self.fluxes.npp * self.fluxes.albranch
                self.fluxes.cpstem = self.fluxes.npp * self.fluxes.alstem
                
                self.fluxes.npbranch = (self.fluxes.npp * self.fluxes.albranch * 
                                        ncbnew)
                self.fluxes.npstemimm = (self.fluxes.npp * self.fluxes.alstem * 
                                         ncwimm)
                self.fluxes.npstemmob = (self.fluxes.npp * self.fluxes.alstem * 
                                        (ncwnew - ncwimm))
                self.fluxes.npcroot = (self.fluxes.npp * self.fluxes.alcroot * 
                                        nccnew)
                
                # Also need to recalculate GPP and thus Ra and return a flag
                # so that we know to recalculate the water balance.
                self.fluxes.gpp = self.fluxes.npp / self.params.cue
                conv = const.G_AS_TONNES / const.M2_AS_HA
                self.fluxes.gpp_gCm2 = self.fluxes.gpp / conv
                self.fluxes.gpp_am_pm[0] = self.fluxes.gpp_gCm2 / 2.0
                self.fluxes.gpp_am_pm[1] = self.fluxes.gpp_gCm2 / 2.0
                
                # New respiration flux
                self.fluxes.auto_resp =  self.fluxes.gpp - self.fluxes.npp
                recalc_wb = True 
                
            ntot -= (self.fluxes.npbranch + self.fluxes.npstemimm +
                     self.fluxes.npstemmob + self.fluxes.npcroot)
            ntot = max(0.0, ntot)
            
            # allocate remaining N to flexible-ratio pools
            self.fluxes.npleaf = (ntot * self.fluxes.alleaf / 
                                 (self.fluxes.alleaf + self.fluxes.alroot *
                                 self.params.ncrfac))
            self.fluxes.nproot = ntot - self.fluxes.npleaf
            
        return recalc_wb 
        
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
        
        rootretransn = self.params.rretrans * rdecay * self.state.rootn
        crootretransn = (self.params.cretrans * self.params.crdecay *
                         self.state.crootn)
        branchretransn = (self.params.bretrans * self.params.bdecay *
                          self.state.branchn)
        stemretransn = (self.params.wretrans * self.params.wdecay *
                        self.state.stemnmob + self.params.retransmob *
                        self.state.stemnmob)
        
        # store for NCEAS output
        self.fluxes.leafretransn = leafretransn
        
        return (leafretransn + rootretransn + crootretransn + branchretransn +
                stemretransn)
        
        
    
    def calculate_nuptake(self, project_day):
        """ N uptake depends on the rate at which soil mineral N is made 
        available to the plants.
        
        Returns:
        --------
        nuptake : float
            N uptake
            
        References:
        -----------
        * Dewar and McMurtrie, 1996, Tree Physiology, 16, 161-171.    
        * Raich et al. 1991, Ecological Applications, 1, 399-429.
            
        """
        if self.control.nuptake_model == 0:
            # Constant N uptake
            nuptake = self.params.nuptakez
        elif self.control.nuptake_model == 1:
            # evaluate nuptake : proportional to dynamic inorganic N pool
            nuptake = self.params.rateuptake * self.state.inorgn
        elif self.control.nuptake_model == 2:
            # N uptake is a saturating function on root biomass following
            # Dewar and McMurtrie, 1996.
            
            # supply rate of available mineral N
            U0 = self.params.rateuptake * self.state.inorgn
            Kr = self.params.kr
            nuptake = max(U0 * self.state.root / (self.state.root + Kr), 0.0)
        elif self.control.nuptake_model == 3:
            # N uptake is a function of available soil N, soil moisture 
            # following a Michaelis-Menten approach 
            # See Raich et al. 1991, pg. 423.
            
            vcn = 1.0 / 0.0215 # 46.4
            arg1 = (vcn * self.state.shootn) - self.state.shoot
            arg2 = (vcn * self.state.shootn) + self.state.shoot
            self.params.ac += self.params.adapt * arg1 / arg2
            self.params.ac = max(min(1.0, self.params.ac), 0.0)
            
            # soil moisture is assumed to influence nutrient diffusion rate
            # through the soil, ks [0,1]
            theta = self.state.pawater_root / self.params.wcapac_root 
            ks = 0.9 * theta**3.0 + 0.1
            
            arg1 = self.params.nmax * ks * self.state.inorgn 
            arg2 = self.params.knl + (ks * self.state.inorgn)
            arg3 = exp(0.0693 * self.met_data['tair'][project_day])
            arg4 = 1.0 - self.params.ac
            nuptake = (arg1 / arg2) * arg3 * arg4
            
            #print self.params.nmax, self.params.knl, ks, exp(0.0693 * tavg) 
            
        else:
            raise AttributeError('Unknown N uptake option')
        
        # Stop N uptake if C:N falls below 10
        #if self.state.plantnc > 0.1:
        #    nuptake = 0.0
        
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
            self.fluxes.cpcroot = self.fluxes.crate * days_left
        else:
            self.fluxes.cpleaf = self.fluxes.npp * self.fluxes.alleaf
            self.fluxes.cproot = self.fluxes.npp * self.fluxes.alroot
            self.fluxes.cpcroot = self.fluxes.npp * self.fluxes.alcroot
            self.fluxes.cpbranch = self.fluxes.npp * self.fluxes.albranch
            self.fluxes.cpstem = self.fluxes.npp * self.fluxes.alstem
            
        # evaluate SLA of new foliage accounting for variation in SLA 
        # with tree and leaf age (Sands and Landsberg, 2002). Assume 
        # SLA of new foliage is linearly related to leaf N:C ratio 
        # via nitfac. Based on date from two E.globulus stands in SW Aus, see
        # Corbeels et al (2005) Ecological Modelling, 187, 449-474.
        # (m2 onesided/kg DW)
        self.params.sla = (self.params.slazero + nitfac *
                          (self.params.slamax - self.params.slazero))
        
        if self.control.deciduous_model:
            if float_eq(self.state.shoot, 0.0):
                self.state.lai = 0.0
            elif self.state.leaf_out_days[doy] > 0.0:               
                
                self.state.lai += (self.fluxes.cpleaf * 
                                  (self.params.sla * const.M2_AS_HA / 
                                  (const.KG_AS_TONNES * self.params.cfracts)) -
                                  (self.fluxes.deadleaves + 
                                   self.fluxes.ceaten) *
                                   self.state.lai / self.state.shoot)
            else:
                self.state.lai = 0.0
        else:
            # update leaf area [m2 m-2]
            if float_eq(self.state.shoot, 0.0):
                self.state.lai = 0.0
            else:
                self.state.lai += (self.fluxes.cpleaf * 
                                  (self.params.sla * const.M2_AS_HA / 
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
        
        if self.state.croot < tolerance:
            self.fluxes.deadcrootn += self.state.crootn
            self.fluxes.deadcroots += self.state.croot
            self.state.croot = 0.0
            self.state.crootn = 0.0
        
        # Not setting these to zero as this just leads to errors with desert
        # regrowth...instead seeding them to a small value with a CN~25.
        
        if self.state.stem < tolerance:     
            self.fluxes.deadstems += self.state.stem
            self.fluxes.deadstemn += self.state.stemn
            self.state.stem = 0.001
            self.state.stemn = 0.00004
            self.state.stemnimm = 0.00004
            self.state.stemnmob = 0.0
        
        # need separate one as this will become very small if there is no
        # mobile stem N
        if self.state.stemnmob < tolerance: 
            self.fluxes.deadstemn += self.state.stemnmob
            self.state.stemnmob = 0.0  
            
        if self.state.stemnimm < tolerance: 
            self.fluxes.deadstemn += self.state.stemnimm
            self.state.stemnimm = 0.00004  
        
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
        self.state.croot += self.fluxes.cpcroot - self.fluxes.deadcroots
        self.state.branch += self.fluxes.cpbranch - self.fluxes.deadbranch
        self.state.stem += self.fluxes.cpstem - self.fluxes.deadstems
        
        # annoying but can't see an easier way with the code as it is.
        # If we are modelling grases, i.e. no stem them without this
        # the sapwood will end up being reduced to a silly number as 
        # deadsapwood will keep being removed from the pool, even though there
        # is no wood. 
        if self.state.stem <= 0.01:
            self.state.sapwood = 0.01
        else:
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
        self.state.crootn += self.fluxes.npcroot - self.params.crdecay * self.state.crootn
        
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
        # how much N we have to allocate so it is impossible (well) to allocate in 
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
        """ Deciduous trees store carbohydrate during the winter which they then
        use in the following year to build new leaves (buds & budburst are 
        implied) 
        """
        # Total C & N storage to allocate annually.
        self.state.cstore += self.fluxes.npp
        self.state.nstore += self.fluxes.nuptake + self.fluxes.retrans 
        self.state.anpp += self.fluxes.npp
        
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

    state.lai = (params.sla * const.M2_AS_HA /
                            const.KG_AS_TONNES / params.cfracts *
                            state.shoot)

    
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
                                params.sla * const.KG_AS_G)
        daylen = day_length(datex, params.latitude)
        state.wtfac_root = 1.0
        #state.lai = laidata[project_day]


        if float_lt(state.lai, params.lai_cover):
            frac_gcover = state.lai / params.lai_cover
        else:
            frac_gcover = 1.0

        state.fpar = ((1.0 - exp(-params.kext *
                                            state.lai / frac_gcover)) *
                                            frac_gcover)



        PG.grow(project_day, datex, fdecay, rdecay)
        print fluxes.gpp / const.HA_AS_M2 * const.TONNES_AS_G



        datex += datetime.timedelta(days=1)
    end_time = time.time()
    sys.stderr.write("\nTotal simulation time: %.1f seconds\n\n" %
                                                    (end_time - start_time))
    
    