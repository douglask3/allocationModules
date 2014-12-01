from math import exp
from dimensionless_variables import dimensionless_variables

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"

class photosythesis(object):
    """ Photosythesis equations used to drive MaxW in McMurtrie et al. (2013).
    """
    def __init__(self, An, N0, Kl, Rleaf, I0, alpha, convfactor):
        self.An			= An
        self.N0			= N0
        self.Kl			= Kl
        self.Rleaf		= Rleaf
        self.I0			= I0
        self.alpha		= alpha
        self.convfactor = convfactor
        self.DV			= dimensionless_variables(An, alpha, Kl, I0, N0)
    	self
    
    # This First section may well be removed when imported to Gday
    def Asat(self, na):    
        return(self.An * (na - self.N0))
    
    def I(self, lai):
        return(self.Kl * self.I0 * exp(-self.Kl * lai))
    
    def Aa(self, LAI, na):
        a = (1.0 / self.Asat(na))+(1.0 / (self.alpha * self.I(LAI)))
        a = (1.0 / a)-self.Rleaf * na
        a = a * self.convfactor
        
        return(a)
        
    def dAdN(self, lai, na):
        Asat= self.Asat(na)
        
        a = (1.0 + Asat / (1.0 + Asat / (self.alpha * self.I(lai)))) ** 2.0
        a = self.An / a
        a = a - self.Rleaf
        a = a * self.convfactor
        
        return(a)
        
    #This section will probably be used
    
    def zetaFun(ltot,nabase):
    	return( (1+self.DV.zeta(nabase)*exp(self.Kl*ltot))**0.5 )
    
    def _atotup1(ltot, nabase):
    	a=self.alpha*self.I0
    	b=1+self.DV.zeta(nabase)
    	
    	return(a*(1-b/self.zetaFun))
    	
    def _atotup2(ltot,nabase):
    	...
    
    def atotup(ltot,nabase):
    	return(self._atotup1(lto,nabase) if self.N0==1 else self._atotup1(lto,nabase) )
    
    def _atotlow1(ltot,nabase):
    	a=-self.zetaFun+self.zetaFun**2
    	a=log(a/self.DV.zeta(nabase))
    	
    	b=self.An.nabase
    	
    	return(b * (ltot-(1/self.Kl)*a))
    	
    def _atotlow2(ltot,nabase):
    	...
    	
    def atotlow (ltot,nabase):
    	return(self._atotlow1(lto,nabase) if self.N0==1 else self._atotlow2(lto,nabase) )
    		
""" References
    ==========
        McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
    from the hypothesis that annual wood production is maximized. New Phytol.
    2013;199(4):981-90. doi:10.1111/nph.12344.
"""