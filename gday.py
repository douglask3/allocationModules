#!/usr/bin/env python
""" G'DAY is a process based model, which runs on a daily timestep and
simulates carbon, nutrient and water state and fluxes. See below for model
description.
"""

#import ipdb
import sys
from math import fabs
import constants as const
from file_parser import initialise_model_data
from plant_growth import PlantGrowth
from print_outputs import PrintOutput
from litter_production import Litter
from soil_cn_model import CarbonSoilFlows, NitrogenSoilFlows
from check_balance import CheckBalance
from utilities import float_eq, calculate_daylength, uniq
from phenology import Phenology

__author__  = "Martin De Kauwe"
__version__ = "1.0 (15.02.2011)"
__email__   = "mdekauwe@gmail.com"


class Gday(object):
    """ The G'DAY (Generic Decomposition And Yield) model.

    GDAY simulates C, N and water cycling between the plant and the soil. The
    model is structured into three plant pools (foliage, wood and fine roots),
    four litter pools (above/below metabolic and structural litter) and three
    soil organic matter (SOM) pools with varying turnover rates (active, slow
    and passive). An adapted implementation of the CENTURY model simulates soil
    carbon and nutrient dynamics. There is an additional simple soil water
    balance module which can be used to limit growth. Model pools can be thought
    of as buckets as they don't have dimensions.

    References:
    ----------
    * Comins, H. N. and McMurtrie, R. E. (1993) Ecological Applications, 3,
      666-681.
    * Medlyn, B. E. et al (2000) Canadian Journal of Forest Research, 30,
      873-888.

    """
    def __init__(self, fname=None, DUMP=False, spin_up=False):

        """ Set up model

        Read meterological forcing file and user config file and adjust the
        model parameters, control or initial state attributes that are used
        within the code.

        Parameters:
        ----------
        fname : string
            filename of model parameters, including path
        chk_cmd_line : logical
            parse the cmd line?
        DUMP : logical
            dump a the default parameters to a file

        Returns:
        -------
        Nothing
            Controlling class of the model, runs things.

        """
        self.day_output = [] # store daily outputs
        (self.control, self.params,
            self.state, self.files,
            self.fluxes, self.met_data,
            self.print_opts) = initialise_model_data(fname, DUMP=DUMP)
        
        if self.control.water_stress == False:
            sys.stderr.write("**** You have turned off the drought stress")
            sys.stderr.write(", I assume you're debugging??!\n")

        # printing stuff
        self.pr = PrintOutput(self.params, self.state, self.fluxes,
                              self.control, self.files, self.print_opts)
        
        # build list of variables to print
        (self.print_state, self.print_fluxes) = self.pr.get_vars_to_print()
        
        # print model defaults
        if DUMP == True:
            self.pr.save_default_parameters()
            sys.exit(0)
        
        self.correct_rate_constants(output=False)

        # class instances
        self.cs = CarbonSoilFlows(self.control, self.params, self.state,
                                  self.fluxes, self.met_data)
        self.ns = NitrogenSoilFlows(self.control, self.params, self.state,
                                    self.fluxes, self.met_data)
        self.lf = Litter(self.control, self.params, self.state, self.fluxes)
        self.pg = PlantGrowth(self.control, self.params, self.state,
                              self.fluxes, self.met_data)
        self.cb = CheckBalance(self.control, self.params, self.state,
                               self.fluxes, self.met_data)
        if self.control.deciduous_model:
            #self.control.alloc_model = "FIXED"
            self.pg.calc_carbon_allocation_fracs(0.0, 0, 0)
            #self.control.alloc_model = "ALLOMETRIC"
            self.pg.allocate_stored_c_and_n(init=True)
            self.P = Phenology(self.fluxes, self.state, self.control,
                               self.params.previous_ncd,
                               store_transfer_len=self.params.store_transfer_len)

        # calculate initial C:N ratios and zero annual flux sums
        self.day_end_calculations(0, INIT=True)
        self.state.pawater_root = self.params.wcapac_root
        self.state.pawater_tsoil = self.params.wcapac_topsoil
        self.spin_up = spin_up
        self.state.sla = self.params.slainit # Specific leaf area (m2/kg DW)
        self.state.lai = (self.params.slainit * const.M2_AS_HA /
                          const.KG_AS_TONNES / self.params.cfracts *
                          self.state.shoot)
                          
    def spin_up_pools(self, tolerance=1E-03):
        """ Spin Up model plant, soil and litter pools.
        -> Examine sequences of 1000 years and check if C pools are changing
           or at steady state to 3 d.p.

        References:
        ----------
        Adapted from...
        * Murty, D and McMurtrie, R. E. (2000) Ecological Modelling, 134,
          185-205, specifically page 196.
        """
        prev_plantc = 9999.9
        prev_soilc = 9999.9
        
        while True:
            if (fabs(prev_plantc - self.state.plantc) < tolerance and
                fabs(prev_soilc - self.state.soilc) < tolerance):
                break
            else:            
                prev_plantc = self.state.plantc
                prev_soilc = self.state.soilc
                self.run_sim() # run the model...
                
                # Have we reached a steady state?
                sys.stderr.write("Spinup: Plant C - %f, Soil C - %f\n" % \
                                (self.state.plantc, self.state.soilc))
        self.print_output_file()
    
    def run_sim(self):
        """ Run model simulation! """
        project_day = 0
        
        # figure out the number of years for simulation and the number of
        # days in each year
        years = uniq(self.met_data["year"])
        days_in_year = [self.met_data["year"].count(yr) for yr in years]
        
        # =============== #
        #   YEAR LOOP     #
        # =============== #
        for i, yr in enumerate(years):
            self.day_output = [] # empty daily storage list for outputs
            daylen = calculate_daylength(days_in_year[i], self.params.latitude)
            if self.control.deciduous_model:
                self.P.calculate_phenology_flows(daylen, self.met_data,
                                            days_in_year[i], project_day)
                self.zero_stuff()
            # =============== #
            #   DAY LOOP      #
            # =============== #  
            for doy in xrange(days_in_year[i]):
                
                # litterfall rate: C and N fluxes
                (fdecay, rdecay) = self.lf.calculate_litter(doy)
                
                # co2 assimilation, N uptake and loss
                self.pg.calc_day_growth(project_day, fdecay, rdecay,
                                        daylen[doy], doy, 
                                        float(days_in_year[i]), i)
            
                # soil C & N model fluxes
                self.cs.calculate_csoil_flows(project_day)
                self.ns.calculate_nsoil_flows(project_day)
    
                # calculate C:N ratios and increment annual flux sums
                self.day_end_calculations(project_day, days_in_year[i])
                
                
                #print self.state.shoot, self.state.lai
                print self.fluxes.gpp * 100, self.state.lai
                # =============== #
                #   END OF DAY    #
                # =============== #
                self.save_daily_outputs(yr, doy+1)
                
                # check the daily water balance
                #self.cb.check_water_balance(project_day)
                
                project_day += 1
            # =============== #
            #   END OF YEAR   #
            # =============== #
            if self.control.deciduous_model:
                self.pg.allocate_stored_c_and_n(init=False)
                
            if self.control.print_options == "DAILY" and self.spin_up == False:
                self.print_output_file()
            
        # close output files
        if self.control.print_options == "END" and self.spin_up == False:
            self.print_output_file()
        self.pr.clean_up()

    def print_output_file(self):
        """ Either print the daily output file (at the end of the year) or
        print the final state + param file. """

        # print the daily output file, this is done once at the end of each yr
        if self.control.print_options == "DAILY":
            self.pr.write_daily_outputs_file(self.day_output)
        
        # print the final state
        elif self.control.print_options == "END":
            if not self.control.deciduous_model:
                # need to save initial SLA to current one!
                conv = const.M2_AS_HA * const.KG_AS_TONNES
                self.params.slainit = (self.state.lai / const.M2_AS_HA *
                                       const.KG_AS_TONNES *
                                       self.params.cfracts /self.state.shoot)

            self.correct_rate_constants(output=True)
            self.pr.save_state()

    def zero_stuff(self):
        self.state.shoot = 0.0
        self.state.shootn = 0.0
        self.state.shootnc = 0.0
        self.state.lai = 0.0
        self.state.cstore = 0.0
        self.state.nstore = 0.0
        self.state.anpp = 0.0
        
    def correct_rate_constants(self, output=False):
        """ adjust rate constants for the number of days in years """
        time_constants = ['rateuptake', 'rateloss', 'retransmob',
                          'fdecay', 'fdecaydry', 'rdecay', 'rdecaydry',
                          'bdecay', 'wdecay', 'sapdecay','kdec1', 'kdec2', 
                          'kdec3', 'kdec4', 'kdec5', 'kdec6', 'kdec7', 
                          'nuptakez']
        conv = const.NDAYS_IN_YR
        
        if output == False:
            for i in time_constants:
                setattr(self.params, i, getattr(self.params, i) / conv)
        else:
            for i in time_constants:
                setattr(self.params, i, getattr(self.params, i) * conv)

    def day_end_calculations(self, prjday, days_in_year=None, INIT=False):
        """Calculate derived values from state variables.

        Parameters:
        -----------
        day : integer
            day of simulation

        INIT : logical
            logical defining whether it is the first day of the simulation

        """
        # update N:C of plant pools
        if float_eq(self.state.shoot, 0.0):
            self.state.shootnc = 0.0
        else:
            self.state.shootnc = self.state.shootn / self.state.shoot
        
        self.state.rootnc = max(0.0, self.state.rootn / self.state.root)
                
        # total plant, soil & litter nitrogen
        self.state.soiln = (self.state.inorgn + self.state.activesoiln +
                            self.state.slowsoiln + self.state.passivesoiln)
        self.state.litternag = self.state.structsurfn + self.state.metabsurfn
        self.state.litternbg = self.state.structsoiln + self.state.metabsoiln
        self.state.littern = self.state.litternag + self.state.litternbg
        self.state.plantn = (self.state.shootn + self.state.rootn +
                             self.state.branchn + self.state.stemn)
        self.state.totaln = (self.state.plantn + self.state.littern +
                             self.state.soiln)

        # total plant, soil, litter and system carbon
        self.state.soilc = (self.state.activesoil + self.state.slowsoil +
                            self.state.passivesoil)
        self.state.littercag = self.state.structsurf + self.state.metabsurf
        self.state.littercbg = self.state.structsoil + self.state.metabsoil
        self.state.litterc = self.state.littercag + self.state.littercbg
        self.state.plantc = (self.state.root + self.state.shoot +
                             self.state.stem + self.state.branch)
        self.state.totalc = (self.state.soilc + self.state.litterc +
                             self.state.plantc)

        # optional constant passive pool
        if self.control.passiveconst == True:
            self.state.passivesoil = self.params.passivesoilz
            self.state.passivesoiln = self.params.passivesoilnz

        if INIT == False:
            #Required so max leaf & root N:C can depend on Age
            self.state.age += 1.0 / days_in_year
               
    def save_daily_outputs(self, year, doy):
        """ Save the daily fluxes + state in a big list.

        This should be a more efficient way to write the daily output in a
        single step at the end of the year.

        Parameters:
        -----------
        project_day : integer
            simulation day
        """
        output = [year, doy]
        for var in self.print_state:
            output.append(getattr(self.state, var))
        for var in self.print_fluxes:
            output.append(getattr(self.fluxes, var))
        self.day_output.append(output)


def main():
    """ run a test case of the gday model """

    # pylint: disable=C0103
    # pylint: disable=C0324

    # timing...
    import time
    start_time = time.time()



    fname = "/Users/mdekauwe/research/NCEAS_face/GDAY_duke_simulation/params/NCEAS_dk_youngforest.cfg"
    #fname = "test.cfg"
    G = Gday(fname)
    G.run_sim()

    end_time = time.time()
    sys.stderr.write("\nTotal simulation time: %.1f seconds\n\n" %
                                                    (end_time - start_time))


def profile_main():
    """ profile code """
    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("main()", globals(), locals())
    print "<pre>"
    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")  # Or cumulative
    stats.print_stats(500)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"


if __name__ == "__main__":

    main()
    #profile_main()
