
import constants as const
from utilities import float_eq, float_ne, float_lt, float_le, float_gt, float_ge

__author__  = "Martin De Kauwe"
__version__ = "1.0 (25.02.2011)"
__email__   = "mdekauwe@gmail.com"


def nc_ratio(x, xn):
    """Calculate nitrogen:carbon ratios"""
    if float_gt(x, 0.0):
        return xn / x
    else:
        return 1E6
        

class Derive(object): 
    def __init__(self, control, params, state, fluxes, met_data): 
        """ 
        Parameters:
        ----------
        control : integers, structure
            model control flags
        params: floats, structure
            model parameters
        state: floats, structure
            model state
        fluxes : floats, structure 
            model fluxes
        met_data : floats, dictionary
            meteorological forcing data
        
        """
        self.params = params
        self.fluxes = fluxes
        self.control = control
        self.state = state
        self.met_data = met_data
        
    def derive_vals_from_state(self, day, date, INIT=False):
        """Calculate derived values from state variables.
        
        Parameters:
        -----------
        day : integer
            day of simulation
        date : date format string
            date object yr/month/day
        INIT : logical
            logical defining whether it is the first day of the simulation
        
        """
        
        ndep = self.met_data['ndep'][day]
        
        # c/n ratios, most of these are just diagnostics, and not used.
        self.state.rootnc = nc_ratio(self.state.root, self.state.rootn)
        
        # just messing with what might happen if canopy directly took up N
        #cnu = 0.48 * ndep
        #self.state.shootn += cnu
        
        self.state.shootnc = nc_ratio(self.state.shoot, self.state.shootn)
        branchnc = nc_ratio(self.state.branch, self.state.branchn)
        stemnc = nc_ratio(self.state.stem, self.state.stemn)
        structsurfnc = nc_ratio(self.state.structsurf, self.state.structsurfn)
        metabsurfnc = nc_ratio(self.state.metabsurf, self.state.metabsurfn)
        structsoilnc = nc_ratio(self.state.structsoil, self.state.structsoiln)
        metabsoilnc = nc_ratio(self.state.metabsoil, self.state.metabsoiln)
        activesoilnc = nc_ratio(self.state.activesoil, self.state.activesoiln)
        slowsoilnc = nc_ratio(self.state.slowsoil, self.state.slowsoiln)
        passivesoilnc = nc_ratio(self.state.passivesoil, self.state.passivesoiln)
        
        # SLA (m2 onesided/kg DW)
        self.state.sla = (self.state.lai / const.M2_AS_HA * 
                            const.KG_AS_TONNES * 
                            self.params.cfracts / self.state.shoot) 
        
        
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
        if self.control.passiveconst != 0:           
            self.state.passivesoil = self.params.passivesoilz
            self.state.passivesoiln = self.params.passivesoilnz 
        
        if INIT == False:
            # day of year 1-365/366
            doy = int(date.strftime('%j'))
            if doy == 1:
                self.state.nepsum = (self.fluxes.nep * const.TONNES_AS_G * 
                                        const.M2_AS_HA)
                self.state.nppsum = (self.fluxes.npp * const.TONNES_AS_G * 
                                        const.M2_AS_HA)
            else:
                self.state.nepsum += (self.fluxes.nep * const.TONNES_AS_G * 
                                        const.M2_AS_HA)
                self.state.nppsum += (self.fluxes.npp * const.TONNES_AS_G * 
                                        const.M2_AS_HA)
        
            # N Net mineralisation, i.e. excess of N outflows over inflows
            self.fluxes.nmineralisation = (ndep + self.fluxes.ngross - 
                                            self.fluxes.nimmob + 
                                            self.fluxes.nlittrelease)
            
            # evaluate c input/output rates for mineral soil and soil+litter 
            # Not used anyway so I have commented them out, diagnostics
            # mineral soil
            #cinsoil = sum(self.fluxes.cstruct) + sum(self.fluxes.cmetab) 
            
            # litter + mineral soil
            #cinlitt = (self.fluxes.deadleaves + self.fluxes.deadroots + 
            #            self.fluxes.deadbranch + self.fluxes.deadstems) 
                        
            # output from mineral soil
            #coutsoil = (self.fluxes.co2_to_air[4] + self.fluxes.co2_to_air[5] + 
            #            self.fluxes.co2_to_air[6]) 
            
            # soil decomposition rate=flux/pool
            #soildecomp = coutsoil / self.state.soilc 
            