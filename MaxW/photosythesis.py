from math 					 import exp, log
from dimensionless_variables import dimensionless_variables
from total_canopy_N_content	 import total_canopy_N_content

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
    	self.a 			= alpha*I0
    	
    	N				= total_canopy_N_content(An, alpha, Kl, I0, N0)
    	self.ntot		= N.ntot
    	self.remainingN = N.remainingN
    
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
    
    def _atotup1(self,ltot, nabase):
    	
    	b=1+self.DV.zeta(nabase)
    	
    	return(self.a*(1-b/self.zetaFun(ltot,nabase)))
    	
    def _atotup2(self,ltot,nabase):
    	b=1-(1/self.DV.ExpKLcrit(ltot,nabase))
    	c=1/self.remainingN(nabase)
    	d=self.DV.zeta(nabase)*exp(self.Kl*ltot)
    	
    	return(self.a*b*(1-1/((c+d)**0.5)))
    	
    def _atotXX_fromN0(self,Fun1,Fun2,*args):
    	return(Fun1(*args) if self.N0==1 else Fun2(*args) )
    
    def atotup(self,*args):
    	return(self._atotXX_fromN0(self._atotup1,self._atotup2,*args))
    
    def _atotlow1(self,ltot,nabase):
    	zetaFun=self.zetaFun(ltot,nabase)
    	a=-zetaFun+zetaFun**2
    	a=log(a/self.DV.zeta(nabase))
    	
    	b=self.An*nabase
    	
    	return(b * (ltot-(1/self.Kl)*a))
    	
    def _atotlow2(self,ltot,nabase):
    	a=self.An*(nabase-self.N0)
    	b=ltot-self.DV.Lcrit(ltot,nabase)
    	
    	zetaFun=self.DV.zeta(nabase)*self.remainingN)
    	
    	c=1+zetaFun*exp(self.Kl*ltot)
    	d=1+zetaFun*self.DV.ExpKLcrit(ltot,nabase)
    	
    	return(a*(b-(1/self.Kl)*log(c/d)))
    	
    	
    def atotlow (self,*args):
    	return(self._atotXX_fromN0(self._atotlow1,self._atotlow2,*args))
    	
    def atot(self,*args):
    	return( self.atotup(*args)+self.atotlow(*args) )
    
    def Atot(self,*args):
    	return( self.convfactor * (self.atot(*args) - self.Rleaf * self.ntot(*args)) )
		
    def Aapt2(lai,ltot,nabase):
    	return(Aa(lai,self.N.Na2(lai,ltot,nabase)))
    	
    
""" References
    ==========
        McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
    from the hypothesis that annual wood production is maximized. New Phytol.
    2013;199(4):981-90. doi:10.1111/nph.12344.
"""