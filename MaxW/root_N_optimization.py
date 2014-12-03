from math import exp,log
from photosythesis import photosythesis
from total_canopy_N_content import total_canopy_N_content
from scipy.optimize import minimize, newton

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class root_N_optimization(object):
    """ Calculation of LAI as uses in McMurtrie et al. (2013).
    
    """
    def __init__(self,D0, R0):
        ## From parameter list
        self.D0		= D0
        self.R0		= R0
    	
    	
    def utot(self, dmax, umax):
    	return(umax*(1-exp(-dmax/2*D0))**2)
    
    
    def rtot1(self, umax, utot):
    	rootU=(utot/umax)**0.5
    
    	a=2*self.R0*self.D0
    	b=rootU/(1-rootU)
    	c=log(1-rootU)
    	
    	return(a*(b+c))
    
    def rtot2(dmax):
    	a=exp(dmax/(2*self.D0))-1
    	b=2*self.R0
    	return(self.R0*(b*b-dmax))
    
    def _rotOpt(dmax,rtot) return( rtot2(dmax) - rtot )
    
    def dmax1(rtot,dmaxsoln=1):
    	newton(self._rotOpt, dmaxsoln, args = (nrtot) )
        
        