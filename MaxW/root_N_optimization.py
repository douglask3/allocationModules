from math import exp,log
from photosythesis import photosythesis
from total_canopy_N_content import total_canopy_N_content
from scipy.optimize import minimize, newton

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"


class root_N_optimization(object):
    """ Calculation of LAI as uses in McMurtrie et al. (2013).
    
    """
    def __init__(self,D0, R0, Nw, CUE, Retrans,
    			 An, N0, Kl, Rleaf, I0, alpha, convfactor):
        ## From parameter list
        self.D0		= D0
        self.R0		= R0
        self.Nw		= Nw
        self.CUE	= CUE
        self.Retrans= Retrans
        self.Tauf	= Tauf
        self.Taur	= Taur
        
        self.atot	= photosythesis(An, N0, Kl, Rleaf, I0, alpha, convfactor).atot
    	self.ntot	= total_canopy_N_content(An, alpha, Kl, I0, N0).ntot
    	
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
    
    def _rotOpt(dmax,rtot) return( self.rtot2(dmax) - rtot )
    
    def dmax1(rtot,dmaxsoln=1):
    	newton(self._rotOpt, dmaxsoln, args = (nrtot) )
      
        
    def DmaxVsLtot(ltot,nabase,nf,nr,Umax1):
    	a=log((umax,Tauf)/(R0.D0))
    	
    	b=(1-self.Retrans)
    	c=self.CUE.slef.convfactor.self.Tauf
    	d=-self.RleafAn/self.DV.zetaFun2(ltot,nabase)
    	e=1/nf
    
    	c=c*d-e
    	
    	b=b/c
    	
    	return(self.D0*(a-log(b+nr)))
    
    def C_Nbal(dmax,ltot,nabase,nf,nr,umax):
    	utot=self.utot(dmax,umax)
    	atot=self.atot(ltot,nabase)
    	ntot=self.ntot(ltot,nabase)
    	rtot=self.rtot2(dmax)
    	
    	a=self.Nw*self.CUE*atot
    	b=ntot/self.Tauf
    	c=1-self.Retrans-self.Nw/nf
    	
    	d=rtot/self.Taur
    	e=(nr-Nw)
    	
    	return(utot-a-b*c-d*e)
   
	def C_Nbal1(ltot,nabase,nf,nr,umax):
 		DVL=self.DmaxVsLtot(ltot,nabase,nf,nr,umax)
 		return(C_Nbal(DVL,ltot,nabase,nf,nr,umax))
 		
 	def cwmax(dmax,ltot,nabase,nf):
 		a=CUE*self.atot(ltot,nabase)
 		b=self.ntot(ltot,nabase)/(nf*self.Tauf)
 		c=self.rtot2(dmax)/self.Taur
 		
 		return(a - b - c)
 	