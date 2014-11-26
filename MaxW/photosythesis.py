""" Estimate daily Carbon fixed and pass around the aboveground portion of the
plant. """
from math import exp

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@students.mq.edu.com"



class Photosythesis(object):
	""" Photosythesis equations used to drive MaxW in McMurtrie et al. (2013).
	
	"""
	def __init__(self,params)
		self.An=params.An
		self.N0=params.N0
		self.Kl=params.Kl
		self.I0=params.I0
		self.alpha=params.alpha
		self.convfactor=params.convfactor
	
	def Asat(self,na):	
		return(self.An*(na-self.N0))
	
	def lightIncientatCanopy(lai):
		return(self.KL*self.I0*exp(-self.KL*lai))
	
	def Aa(self,LAI,na):
		a=(1/Asat(na))+(1/self.alpha*lightIncientatCanopy(lai))
		a=(1/a)-self.Rleaf*na
		a=a*self.convfactor
		
		
	
	


""" References
	==========
		McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
	from the hypothesis that annual wood production is maximized. New Phytol.
	2013;199(4):981-90. doi:10.1111/nph.12344.
"""