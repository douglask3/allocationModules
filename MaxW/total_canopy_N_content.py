from dimensionless_variables import dimensionless_variables
#from math import exp,log

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class total_canopy_N_content(object):
    """ Some variables used to in MaxW equations McMurtrie et al. (2013).
    
    """
    def __init__(self, An, alpha, Kl, I0, N0, nabase, ltot):

        self.N0     = N0
        self.alpha  = alpha
        self.I0     = I0
        self.An     = An
        
        self.DV     = dimensionless_variables(An, alpha, Kl, I0, N0, nabase, ltot)
        self.Lcrit  = self.DV.Lcrit(ltot,nabase)
        
    def ntot(ltot, nabase):
        a = self.alpha * self.I0 / self.An
        b = 1.0 - self.N0 / nabase * self.DV.ExpKlcrit_denominator
        c = 1.0 - (1.0 /self.DV.ExpKLcrit(ltot, nabase))
        d = nabase * ltot
        e = nabase - self.No
        f = self.DV.Lcrit(ltot, nabse)
        
        return( a *  b * c + d - e * f)
        
    def ntot2(ltot, nabase):
        return(ntot(ltot, nabase) if self.DV.Lcrit(ltot, nabse) > 0 else ltot * nabase )
        