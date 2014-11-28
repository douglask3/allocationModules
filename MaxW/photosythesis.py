from math import exp

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@students.mq.edu.com"


class photosythesis(object):
	""" Photosythesis equations used to drive MaxW in McMurtrie et al. (2013).
	
	"""
	def __init__(self, An, N0, Kl, Rleaf, I0, alpha, convfactor):
		self.An		= An
		self.N0		= N0
		self.Kl		= Kl
		self.Rleaf	= Rleaf
		self.I0		= I0
		self.alpha	= alpha
		self.convfactor=convfactor
	
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
""" References
	==========
		McMurtrie RE, Dewar RC. New insights into carbon allocation by trees
	from the hypothesis that annual wood production is maximized. New Phytol.
	2013;199(4):981-90. doi:10.1111/nph.12344.
"""