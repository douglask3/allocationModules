from math import exp,log

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class dimensionless_variables(object):
    """ Some variables used to in MaxW equations McMurtrie et al. (2013).
    
    """
    def __init__(self, An, alpha, Kl, I0, N0, nabase, ltot):
        ## From parameter list
        self.An         = An
        self.alpha      = alpha
        self.Kl         = Kl
        self.I0         = I0
        self.N0         = N0
        
        ## Not from paramter list
        self.zeta       = self.zeta(nabase)
        self.ExpKlcrit_denominator = self.ExpKlcrit_denominator(ltot,nabase)
        self.ExpKLcrit0 = self.ExpKLcrit0(ltot, nabase)
        self.Lcrit0     = self.Lcrit0(ltot, nabase)
        
    
    def zeta(self, nabase):    
        return(self.An*nabase / (self.alpha * self.Kl * self.I0))
    
    def ExpKlcrit_denominator(ltot,nabase):
         a = (1.0 - self.N0 / nabase)
         b = self.zeta * exp(self.Kl * ltot)
         return( (b + 1.0 / a)** (0.5) - 1.0 )
    
    def ExpKLcrit0(self, ltot, nabase):
        num = self.zeta * (1.0 - (self.N0 / nabase))
        return( self.ExpKlcrit0_denominator / num )
        
    def Lcrit0(self,ltot,nabase):
        return( (1.0 / self.Kl) * log(self.ExpKLcrit0) )
        
    def Lcrit(self):
        return(0.0 if self.Lcrit0  < 0.0 else self.Lcrit0)
        
    def ExpKLcrit(self):
        return(1.0 if self.Lcrit0 < 0.0 else self.ExpKLcrit0)
        
""" References
    ==========
        McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
    from the hypothesis that annual wood production is maximized. New Phytol.
    2013;199(4):981-90. doi:10.1111/nph.12344.
"""