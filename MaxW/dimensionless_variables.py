from math import exp,log

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class dimensionless_variables(object):
    """ Some variables used to in MaxW equations McMurtrie et al. (2013).
    
    """
    def __init__(self, An, alpha, Kl, I0, N0):
        ## From parameter list
        self.An         = An
        self.alpha      = alpha
        self.Kl         = Kl
        self.I0         = I0
        self.N0         = N0
        
    
    def zeta(self, nabase):    
        return(self.An*nabase / (self.alpha * self.Kl * self.I0))
    
    def ExpKlcrit_denominator(self,ltot,nabase):
        a = (1.0 - self.N0 / nabase)
        b = self.zeta(nabase) * exp(self.Kl * ltot)
        return( (b + 1.0 / a)** (0.5) - 1.0 )
    
    def _ExpKLcrit0(self, ltot, nabase):
        num  = self.zeta(nabase) * (1.0 - (self.N0 / nabase))
        return( self.ExpKlcrit_denominator(ltot, nabase) / num )
        
    def _Lcrit0(self,ltot,nabase):
        ExpKLcrit0 = self._ExpKLcrit0(ltot, nabase)
        return( (1.0 / self.Kl) * log(ExpKLcrit0) )
        
    def Lcrit(self, ltot, nabase):
        Lcrit0     = self._Lcrit0(ltot, nabase)
        return(0.0 if Lcrit0  < 0.0 else Lcrit0)
        
    def ExpKLcrit(self, ltot, nabase):
        ExpKLcrit0 = self._ExpKLcrit0(ltot, nabase)
        Lcrit0     = self._Lcrit0(ltot, nabase)
        return(1.0 if Lcrit0 < 0.0 else ExpKLcrit0)

""" References
    ==========
        McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
    from the hypothesis that annual wood production is maximized. New Phytol.
    2013;199(4):981-90. doi:10.1111/nph.12344.
"""