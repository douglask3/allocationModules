from math                    import exp, log
from dimensionless_variables import dimensionless_variables
from root_N_optimization     import root_N_optimization

__author__  = "Douglas Kelley"
__email__   = "douglas.kelley@mq.edu.com"

class Nuptake(object):
    """ Photosythesis equations used to drive MaxW in McMurtrie et al. (2013).
    """
    def __init__(self, D0, R0, Retrans, Nw):
    
    self.rtot       = root_N_optimization(D0, R0).rtot1
    self.Retrans    = Retrans
    self.Tauf      	= Tauf    
    self.Nw         = Nw
    
    # This First section may well be removed when imported to Gday
    
    def _UtotOpt(Utotsol,umax,rtot):
        return( self.rtot(umax,Utotsol) - rtot )
    
    def Utot(self, rtot,umax,Utotsoln=.5):    
        Utotsoln = Utotsoln*umax
        
        return( newton(self._UtotOpt, Utotsoln, args = (umax,rtot) ) )
    
    def Phi(cw,nr,ntot,rtot,umax):
        a = ntot.(1-self.Retrans)/self.Tauf
        b = rtot*nr/self.Tauf
        c = cw*self.Nw
        
        return( (a + b + c)/umax )
        
    