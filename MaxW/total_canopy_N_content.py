from dimensionless_variables import dimensionless_variables

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class total_canopy_N_content(object):
    """ Some variables used to in MaxW equations McMurtrie et al. (2013).
    
    """
    def __init__(self, An, alpha, Kl, I0, N0):

        self.N0     = N0
        self.alpha  = alpha
        self.Kl     = Kl
        self.I0     = I0
        self.An     = An
        self.DV     = dimensionless_variables(self.An, self.alpha, self.Kl, self.I0, self.N0)
        
    def ntot(self,ltot, nabase):
             
        a = self.alpha * self.I0 / self.An
        b = self.DV.ExpKlcrit_denominator(ltot,nabase)
        c = 1.0 - (1.0 /self.DV.ExpKLcrit(ltot, nabase))
        d = nabase * ltot
        e = nabase - self.N0
        f =self.DV.Lcrit(ltot,nabase)
        
        return( a *  b * c + d - e * f)
        
    def ntot2(self,ltot, nabase):
        return(ntot(ltot, nabase) if self.DV.Lcrit(ltot, nabse) > 0 else ltot * nabase )
        