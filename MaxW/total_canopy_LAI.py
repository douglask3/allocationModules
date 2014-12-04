from math import exp,log
from photosythesis import photosythesis
from total_canopy_N_content import total_canopy_N_content
from scipy.optimize import minimize, newton

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class total_canopy_LAI(object):
    """ Calculation of LAI as uses in McMurtrie et al. (2013).
    
    """
    def __init__(self, An, alpha, Kl, I0, N0, Rleaf, convfactor):
        ## From parameter list
        self.An         = An
        self.alpha      = alpha
        self.Kl         = Kl
        self.I0         = I0
        self.N0         = N0
        self.ntot       = total_canopy_N_content(An, alpha, Kl, I0, N0).ntot
        self.Atot       = photosythesis( An, N0, Kl, Rleaf, I0, alpha, convfactor).Atot
        
    def _N(self, ltot, nabase, ntot0):
        return(self.ntot(ltot, nabase) - ntot0)
    
    def Ltotopt(self, ntot, nabase, ltotsoln = 3):
        return( newton(self._N, ltotsoln, args = (nabase, ntot) ) )

    def AtotVsNtot(self, ntot, nabase):
        ltotopt = self.Ltotopt(ntot, nabase)
        return( self.Atot(ltotopt, nabase) )
        
""" References
    ==========
        McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
    from the hypothesis that annual wood production is maximized. New Phytol.
    2013;199(4):981-90. doi:10.1111/nph.12344.
"""