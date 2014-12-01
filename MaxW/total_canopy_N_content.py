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
        
    def ntot(ltot, nabase):
        DV = dimensionless_variables(self.An, self.alpha, self.Kl, self.I0, self.N0,
             nabase, ltot)
             
        a = self.alpha * self.I0 / self.An
        b = 1.0 - self.N0 / nabase * DV.ExpKlcrit_denominator
        c = 1.0 - (1.0 /DV.ExpKLcrit(ltot, nabase))
        d = nabase * ltot
        e = nabase - self.No
        f = DV.Lcrit
        
        return( a *  b * c + d - e * f)
        
    def ntot2(ltot, nabase):
        return(ntot(ltot, nabase) if self.DV.Lcrit(ltot, nabse) > 0 else ltot * nabase )
        