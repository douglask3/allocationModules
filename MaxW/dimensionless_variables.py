
from math import exp,log

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@students.mq.edu.com"


class dimensionless_variables(object):
	""" Some variables used to in MaxW equations McMurtrie et al. (2013).
	
	"""
	def __init__(self,alpha,Kl,I0,N0,nabase,ltot):
		## From parameter list
		self.alpha=alpha
		self.Kl=Kl
		self.I0=I0
		self.N0=N0
		
		## Not from paramter list
		self.zeta=self.zeta(nabase)
		self.ExpKLcrit0=self.ExpKLcrit0(ltot,nabase)
		self.Lcrit0=self.Lcrit0(ltot,nabase)
		
	
	def zeta(self,nabase):	
		return(An*nabase/(alpha*Kl*I0))
	
	def ExpKLcrit0(ltot,nabase):
	    a=(1-N0/nabase)
	    b=self.zeta*exp(self.Kl-ltot)
	    
	    den=(b+1/a)**(0.5)-1
	    num=self.zeta*(1-(N0/nabase))
	    return(den/num)
	    
	def Lcrit0(ltot,nabase):
	    return((1/self.Kl)*log(self.ExpKLcrit0))
	    
	def Lcrit():
	    if self.Lcrit0<0: return(0) else: return(self.Lcrit0)
	    
	def ExpKLcrit():
	    if self.Lcrit0<0: return(1) else: return(self.ExpKLcrit0(ltot,nabase))
		
""" References
	==========
		McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
	from the hypothesis that annual wood production is maximized. New Phytol.
	2013;199(4):981-90. doi:10.1111/nph.12344.
"""