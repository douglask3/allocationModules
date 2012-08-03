""" Carbon production module, call photosynthesis model """

import math

import constants as const
from utilities import float_eq, float_lt, float_gt, day_length
from bewdy import Bewdy
from plant_production_mcmurtrie import PlantProdModel
from water_balance import WaterBalance, WaterLimitedNPP
from mate import Mate

__author__  = "Martin De Kauwe"
__version__ = "1.0 (23.02.2011)"
__email__   = "mdekauwe@gmail.com"


class PlantGrowth(object):
    """ G'DAY plant growth module.

    Calls photosynthesis model, water balance and evolve plant state.
    Pools recieve C through allocation of accumulated photosynthate and N
    from both soil uptake and retranslocation within the plant.

    Key feedback through soil N mineralisation and plant N uptake

    * Note met_forcing is an object with radiation, temp and precip data
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
        self.pp = PlantProdModel(self.control, self.params, self.state,
                                 self.fluxes, self.met_data)
        self.wl = WaterLimitedNPP(self.control, self.params, self.state,
                                  self.fluxes)

        self.mt = Mate(self.control, self.params, self.state, self.fluxes,
                       self.met_data)

    def grow(self, project_day, fdecay, rdecay, daylen, doy, days_in_yr):
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

        # calculate water balance and adjust C production for any water stress.
        # If we are using the MATE model then water stress is applied directly
        # through the Ci:Ca reln, so do not apply any scalar to production.
        if self.control.water_model == 1:
            self.wb.calculate_water_balance(project_day, daylen)
            # adjust carbon production for water limitations, all models except
            # MATE!
            if self.control.assim_model != 7:
                self.wl.adjust_cproduction(self.control.water_model)

        # leaf N:C as a fraction of Ncmaxyoung, i.e. the max N:C ratio of
        # foliage in young stand
        nitfac = min(1.0, self.state.shootnc / self.params.ncmaxfyoung)
        
        if not self.control.deciduous_model:
            # figure out allocation fractions for C for the evergreen model. For
            # the deciduous model these are calculated at the annual time step.
            self.allocate_carbon(nitfac)
           
        # Distribute new C and N through the system
        self.carbon_distribution(nitfac, doy, days_in_yr)
        
        (ncbnew, ncwimm, ncwnew) = self.calculate_ncwood_ratios(nitfac)
        self.nitrogen_distribution(ncbnew, ncwimm, ncwnew, fdecay, rdecay, doy)
        
        
        self.update_plant_state(fdecay, rdecay)
         
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

        # leaf nitrogen content
        if self.state.lai > 0.0:
            # Leaf N content (g m-2)                       
            
            self.state.ncontent = (self.state.shootnc * self.params.cfracts /
                                   self.state.sla * const.KG_AS_G)
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
            self.state.light_interception = ((1.0 - math.exp(-self.params.kext *
                                             self.state.lai / frac_gcover)) *
                                             frac_gcover)
        else:
            self.state.light_interception = 0.0

        # Calculate the soil moisture availability factors [0,1] in the topsoil
        # and the entire root zone
        (self.state.wtfac_tsoil, 
            self.state.wtfac_root) = self.wb.calculate_soil_water_fac()
        
        # Estimate photosynthesis using an empirical model
        if self.control.assim_model >=0 and self.control.assim_model <= 4:
            self.pp.calculate_photosynthesis(project_day)
        # Estimate photosynthesis using the mechanistic BEWDY model
        elif self.control.assim_model >=5 and self.control.assim_model <= 6:
            # calculate plant C uptake using bewdy
            self.bw.calculate_photosynthesis(frac_gcover, project_day, daylen)
        # Estimate photosynthesis using the mechanistic MATE model. Also need to
        # calculate a water availability scalar to determine Ci:Ca reln.
        elif self.control.assim_model ==7:
            self.mt.calculate_photosynthesis(project_day, daylen)
        else:
            raise AttributeError('Unknown assimilation model')

    def allocate_carbon(self, nitfac):
        """Carbon allocation fractions to move photosynthate through the plant.
        Allocations to foliage tends to decrease with stand age and wood stock
        increases (Makela and Hari, 1986; Cannell and Dewar, 1994; 
        Magnani et al, 2000). In stressed (soil/nutrient) regions fine root 
        allocations increases.

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
        alroot_exudate : float
            allocation fraction for root exudate 
       
        References:
        -----------
        McMurtrie, R. E. et al (2000) Plant and Soil, 224, 135-152.
        """
        self.state.alleaf = (self.params.callocf + nitfac *
                            (self.params.callocf - self.params.callocfz))
    
        self.state.alroot = (self.params.callocr + nitfac *
                            (self.params.callocr - self.params.callocrz))

        self.state.albranch = (self.params.callocb + nitfac *
                              (self.params.callocb - self.params.callocbz))
        
        # Remove some of the allocation to wood and instead allocate it to
        # root exudation. Following McMurtrie et al. 2000
        self.state.alroot_exudate = self.params.callocrx
        
        # allocate remainder to stem
        self.state.alstem = (1.0 - self.state.alleaf - self.state.alroot - 
                             self.state.albranch - self.state.alroot_exudate)
        
    def nitrogen_distribution(self, ncbnew, ncwimm, ncwnew, fdecay, rdecay, doy):
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
        self.fluxes.retrans = self.nitrogen_retrans(fdecay, rdecay)
        self.fluxes.nuptake = self.calculate_nuptake()
        
        # N lost from system is proportional to the soil inorganic N pool, 
        # where the rate constant empirically defines gaseous and leaching 
        # losses, see McMurtrie et al. 2001.
        self.fluxes.nloss = self.params.rateloss * self.state.inorgn
    
        # total nitrogen to allocate 
        ntot = self.fluxes.nuptake + self.fluxes.retrans
        
        # N flux into root exudation, see McMurtrie et al. 2000
        #self.fluxes.nrootexudate = (self.fluxes.npp * alroot_exudate * 
        #                            self.params.vxfix)
        self.fluxes.nrootexudate = 0.0
        
        if self.control.deciduous_model:
            
            # allocate N to pools with fixed N:C ratios
            # N flux into new ring (immobile component -> structrual components)
            self.fluxes.npstemimm = self.fluxes.cpstem * ncwimm
    
            # N flux into new ring (mobile component -> can be retrans for new
            # woody tissue)
            self.fluxes.npstemmob = self.fluxes.cpstem * (ncwnew - ncwimm)
            self.fluxes.npbranch = 0.0    
            self.fluxes.nproot = self.fluxes.cproot * self.state.rootnc
            
            if self.state.growing_days[doy] < -900.0:
                self.fluxes.npleaf = self.state.left_over_n 
            else:

                self.fluxes.npleaf = (self.fluxes.lnrate * self.state.growing_days[doy])
           
           
        else:
            # allocate N to pools with fixed N:C ratios
            
            # N flux into new ring (immobile component -> structrual components)
            self.fluxes.npstemimm = self.fluxes.npp * self.state.alstem * ncwimm
    
            # N flux into new ring (mobile component -> can be retrans for new
            # woody tissue)
            self.fluxes.npstemmob = self.fluxes.npp * self.state.alstem * (ncwnew - ncwimm)
            self.fluxes.npbranch = self.fluxes.npp * self.state.albranch * ncbnew
            
            # If we have allocated more N than we have available 
            #  - cut back N prodn
            arg = (self.fluxes.npstemimm + self.fluxes.npstemmob +
                   self.fluxes.npbranch + self.fluxes.nrootexudate)
    
            if float_gt(arg, ntot) and not self.control.fixleafnc:
                self.fluxes.npp *= (ntot / (self.fluxes.npstemimm +
                                    self.fluxes.npstemmob + 
                                    self.fluxes.npbranch + 
                                    self.fluxes.nrootexudate))
                self.fluxes.npbranch = self.fluxes.npp * self.state.albranch * ncbnew
                self.fluxes.npstemimm = self.fluxes.npp * self.state.alstem * ncwimm
                self.fluxes.npstemmob = (self.fluxes.npp * self.state.alstem * 
                                        (ncwnew - ncwimm))
                self.fluxes.nrootexudate = (self.fluxes.npp * self.state.alroot_exudate * 
                                            self.params.vxfix)
                
            ntot -= (self.fluxes.npbranch + self.fluxes.npstemimm +
                        self.fluxes.npstemmob + self.fluxes.nrootexudate)
            
            # allocate remaining N to flexible-ratio pools
            self.fluxes.npleaf = (ntot * self.state.alleaf / 
                                 (self.state.alleaf + self.state.alroot *
                                 self.params.ncrfac))
            self.fluxes.nproot = ntot - self.fluxes.npleaf
        
    def nitrogen_retrans(self, fdecay, rdecay):
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
            arg1 = (self.fluxes.leafretransn  +
                    self.params.rretrans * rdecay * self.state.rootn +
                    self.params.bretrans * self.params.bdecay * self.state.branchn)
            arg2 = (self.params.wretrans * self.params.wdecay *
                    self.state.stemnmob + self.params.retransmob *
                    self.state.stemnmob)
        else:
            arg1 = (self.params.fretrans * fdecay * self.state.shootn +
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
    
    def carbon_distribution(self, nitfac, doy, days_in_yr):
        """ C distribution - allocate available C through system

        Parameters:
        -----------
        nitfac : float
            leaf N:C as a fraction of 'Ncmaxfyoung' (max 1.0)
        
        References:
        -----------
        
        * Hale, M. G. et al. (1981) Factors affecting root exudation and 
          significance for the rhizosphere ecoystems. Biological and chemical 
          interactions in the rhizosphere. Stockholm. Sweden: Ecological 
          Research Committee of NFR. pg. 43--71.
        * Lambers, J. T. and Poot, P. (2003) Structure and Functioning of 
          Cluster Roots and Plant Responses to Phosphate Deficiency.
        * Martin, J. K. and Puckjeridge, D. W. (1982) Carbon flow through the 
          rhizosphere of wheat crops in South Australia. The cyclcing of carbon,
          nitrogen, sulpher and phosphorous in terrestrial and aquatic
          ecosystems. Canberra: Australian Academy of Science. pg 77--82.
        * McMurtrie, R. E. et al (2000) Plant and Soil, 224, 135-152.
        
        Also see:
        * Rovira, A. D. (1969) Plant Root Exudates. Botanical Review, 35, 
          pg 35--57.
        """
        if self.control.deciduous_model:
            if self.state.growing_days[doy] < -900.0:
                self.fluxes.cpleaf = self.state.left_over_c
               
            else:
                self.fluxes.cpleaf = self.fluxes.lrate * self.state.growing_days[doy]
                
            self.fluxes.cpbranch = 0.0
            self.fluxes.cpstem = self.fluxes.wrate * self.state.growing_days[doy]
            self.fluxes.cproot = self.state.c_to_alloc_root * 1.0 / days_in_yr
        else:
            self.fluxes.cpleaf = self.fluxes.npp * self.state.alleaf
            self.fluxes.cproot = self.fluxes.npp * self.state.alroot
            self.fluxes.cpbranch = self.fluxes.npp * self.state.albranch
            self.fluxes.cpstem = self.fluxes.npp * self.state.alstem
        print self.fluxes.cpleaf
        # C flux into root exudation, see McMurtrie et al. 2000. There is no 
        # reference given for the 0.15 in McM, however 14c work by Hale et al and
        # Martin and Puckeridge suggest values range between 10-20% of NPP. So
        # presumably this is where this values of 0.15 (i.e. the average) comes
        # from
        #self.fluxes.cprootexudate = self.fluxes.npp * alroot_exudate
        self.fluxes.cprootexudate = 0.0
        
        # rhizresp = 0.5, unless changed of course! 1/3--2/3 of C
        # fixed by plants is respired, so assuming a value of 0.5, i.e. the avg.
        # (Lambers and Poot, 2003)
        #self.fluxes.microbial_resp = (self.fluxes.cprootexudate * 
        #                                self.params.rhizresp)
        #self.fluxes.cprootexudate -= self.fluxes.microbial_resp
        
        # evaluate SLA of new foliage accounting for variation in SLA 
        # with tree and leaf age (Sands and Landsberg, 2002). Assume 
        # SLA of new foliage is linearly related to leaf N:C ratio 
        # via nitfac
        sla_new = (self.params.slazero + nitfac *
                  (self.params.slamax - self.params.slazero))
        sla_new_tonnes_ha_C = (sla_new * const.M2_AS_HA / 
                             (const.KG_AS_TONNES * self.params.cfracts))
        
        
        if self.control.deciduous_model:
            if self.state.shoot == 0.0:
                self.state.lai = 0.0
            elif self.state.leaf_out_days[doy] > 0.0:
                self.state.lai += (self.fluxes.cpleaf * sla_new_tonnes_ha_C -
                                  (self.fluxes.deadleaves + self.fluxes.ceaten) *
                                   self.state.lai / self.state.shoot) 
                
                """
                sla_tonnes_ha_C = (self.state.sla * const.M2_AS_HA / 
                                   (const.KG_AS_TONNES * self.params.cfracts))
                self.state.lai = self.state.shoot * sla_tonnes_ha_C
                """
            else:
                self.state.lai = 0.0
        else:
            # update leaf area [m2 m-2]
            self.state.lai += (self.fluxes.cpleaf * sla_new_tonnes_ha_C -
                               (self.fluxes.deadleaves + self.fluxes.ceaten) *
                                self.state.lai / self.state.shoot)
            
            #(Cpleaf * sla_new_tonnes_ha_C - Deadleaves * Lai / Shoot ) 
        
        
    def update_plant_state(self, fdecay, rdecay):
        """ Daily change in C content

        Parameters:
        -----------
        fdecay : float
            foliage decay rate
        rdecay : float
            fine root decay rate

        """
        self.state.shoot += (self.fluxes.cpleaf - self.fluxes.deadleaves -
                                self.fluxes.ceaten)
        self.state.root += self.fluxes.cproot - self.fluxes.deadroots
        self.state.branch += self.fluxes.cpbranch - self.fluxes.deadbranch
        self.state.stem += self.fluxes.cpstem - self.fluxes.deadstems
        
        if self.control.deciduous_model:
            self.state.shootn += (self.fluxes.npleaf - 
                                 (self.fluxes.deadleafn - self.fluxes.neaten))
        else:
            self.state.shootn += (self.fluxes.npleaf - 
                                  fdecay * self.state.shootn - 
                                  self.fluxes.neaten)
        self.state.shootn = max(0.0, self.state.shootn)
        
        self.state.rootn += self.fluxes.nproot - rdecay * self.state.rootn
        self.state.branchn += (self.fluxes.npbranch - self.params.bdecay *
                                self.state.branchn)
        self.state.stemnimm += (self.fluxes.npstemimm - self.params.wdecay *
                                self.state.stemnimm)
        self.state.stemnmob += (self.fluxes.npstemmob - self.params.wdecay *
                                self.state.stemnmob -
                                self.params.retransmob * self.state.stemnmob)
        self.state.stemn = self.state.stemnimm + self.state.stemnmob
        
        
        
        if self.control.deciduous_model:
            # update annual fluxes - store for next year
            self.state.clabile_store += self.fluxes.npp
            self.state.aroot_uptake += self.fluxes.nuptake
            self.state.aretrans += self.fluxes.retrans
            self.state.anloss += self.fluxes.nloss
            self.calculate_cn_store()
        else:
            self.calculate_cn_store()
            # maximum leaf n:c ratio is function of stand age
            #  - switch off age effect by setting ncmaxfyoung = ncmaxfold
            age_effect = ((self.state.age - self.params.ageyoung) / 
                            (self.params.ageold - self.params.ageyoung))
            
            ncmaxf = (self.params.ncmaxfyoung - (self.params.ncmaxfyoung -
                        self.params.ncmaxfold) * age_effect)
                   
            if float_lt(ncmaxf, self.params.ncmaxfold):
                ncmaxf = self.params.ncmaxfold
    
            if float_gt(ncmaxf, self.params.ncmaxfyoung):
                ncmaxf = self.params.ncmaxfyoung
    
            # if foliage or root n:c ratio exceeds its max, then nitrogen uptake is
            # cut back n.b. new ring n/c max is already set because it is related
            # to leaf n:c
            extrar = 0.
            extras = 0.
            if float_gt(self.state.shootn, (self.state.shoot * ncmaxf)):
                extras = self.state.shootn - self.state.shoot * ncmaxf
    
                #n uptake cannot be reduced below zero.
                if float_gt(extras, self.fluxes.nuptake):
                    extras = self.fluxes.nuptake
    
                self.state.shootn -= extras
                self.fluxes.nuptake -= extras
    
            ncmaxr = ncmaxf * self.params.ncrfac  # max root n:c
    
            if float_gt(self.state.rootn, (self.state.root * ncmaxr)):
                extrar = self.state.rootn - self.state.root * ncmaxr
    
                #n uptake cannot be reduced below zero.
                if float_gt((extras + extrar), self.fluxes.nuptake):
                    extrar = self.fluxes.nuptake - extras
    
                self.state.rootn -= extrar
                self.fluxes.nuptake -= extrar 
            
    def calculate_cn_store(self, tolerance=1.0E-05):        
        cgrowth = (self.fluxes.cpleaf + self.fluxes.cproot + 
                   self.fluxes.cpbranch + self.fluxes.cpstem)
        ngrowth = (self.fluxes.npleaf + self.fluxes.nproot + 
                   self.fluxes.npbranch + self.fluxes.npstemimm + 
                   self.fluxes.npstemmob)
        
        if self.control.deciduous_model:
            # C storage as TNC
            store = self.state.clabile_store - cgrowth
            if math.fabs(store) <= tolerance:
                store = 0.0
            self.state.cstore += store
            
            # N storage
            store = self.state.aroot_uptake + self.state.aretrans - ngrowth
            if math.fabs(store) <= tolerance:
                store = 0.0
            self.state.nstore += store
            
            #print self.state.cstore, store, self.state.clabile_store - cgrowth
        else:            
            # C storage as TNC
            store = self.fluxes.npp - cgrowth
            if math.fabs(store) <= tolerance:
                store = 0.0
            self.state.cstore += store
            
            # N storage
            store = self.fluxes.nuptake + self.fluxes.retrans - ngrowth
            if math.fabs(store) <= tolerance:
                store = 0.0
            self.state.nstore += store        


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

        state.light_interception = ((1.0 - math.exp(-params.kext *
                                            state.lai / frac_gcover)) *
                                            frac_gcover)



        PG.grow(project_day, datex, fdecay, rdecay)
        print fluxes.gpp / const.HA_AS_M2 * const.TONNES_AS_G



        datex += datetime.timedelta(days=1)
    end_time = time.time()
    sys.stderr.write("\nTotal simulation time: %.1f seconds\n\n" %
                                                    (end_time - start_time))
    
    