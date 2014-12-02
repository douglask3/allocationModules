from math import pi
import matplotlib.pyplot as plt
from numpy import arange

## Photosynthesis & C balance
w       = 0.49          # C content of
Mastar  = 0.181         # Leaf mass per unit area at base of canopy (kg DM/m2)
Nf      = (14/w)*0.001  # Leaf N:C ratio (g N / g C)
Nabase  = Nf*Mastar*w   # Fix Narea at base of canopy (kg N/m2)
Kl      = 0.43          # Light extinction coefft
Ntot    = 21.6E-3       # Total canopy N content (kgN/m2) 
An      = 2.09E-3       # Slope of Amax vs Narea relationship (mol/kgN/s)
N0      = 4E-4          # Minimum N area for photosynthesis (kgN/m2)
alpha   = 0.06          # Quantum efficiency
Rleaf   = 0.0           # 0.09*2E-3Leaf maintenance respiration rate (mol/kgN/s)
I0      = 611E-6        # Incident photosynthetically active radiation (mol/m2/s),
CUE     = 0.45          # Using Mcad corrected values
Tauf    = 8             # Leaf lifespan (yrs)
Taur    = 1             # Root lifespan (yrs)

## Root & N uptake parameters
r0      = 0.017         # root radius (cm)
pr      = 0.38          # root tissue density (g/cm3)
Lr0     = 0.76678       # root length density at half max U /cm2
R0      = pi*r0**2*pr*Lr0*1000*w
                        # root mass density at half max kg C /m3
Umax1   = 0.012         # Annual supply of available soil N. aka Potential annual N uptake (gN/m2 ground/year)
Umax2   = 0.008     
D0      = 0.6           # Length scale for exponential decline (m)
Nr      = 0.015         # Root N:C ratio
                        # ~7E-3/w 
Nw      = 0.003         # Root N:C ratio
                        # ~1.5E-3/w 
Retrans = 0.5           # Fraction of leaf N retranslocated at senescence


## Conversion factors
Daysperyear = 209       # Growing season length (days)
Hoursperday = 14.14     # Daylight length (hrs)
Convfactor  = Daysperyear*Hoursperday*60*60*12*1E-3

############################################################
 
def printNewLine(txt): print("\n"+txt+":\t")

def pltFunFromX(x,FUN,nabase,scale=1,*args):
	y = [scale*FUN(i, nabase) for i in x]
	plt.plot(x,y,*args)

from photosythesis import photosythesis

A=photosythesis(An, N0, Kl, Rleaf, I0, alpha, Convfactor)

def when_Ltot_is_X_and_nabase__is_NaBase_Expect(x,vs,**FUNs):
	strng = "when ltot=" + str(x) + " and nabase=Nabase, Expect:"
	keys  = FUNs.keys()
	
	for i in range(len(vs)): strng = strng + "\n\t" + str(vs[i]) + " for " + keys[i]
	printNewLine(strng)
	
	for i in FUNs: print FUNs[i](x, Nabase)
	
def when_Ltot_is_5_and_05(vs5,vs05,**FUNs):
	when_Ltot_is_X_and_nabase__is_NaBase_Expect(5.0, vs5  ,**FUNs)
	when_Ltot_is_X_and_nabase__is_NaBase_Expect(0.5, vs05 ,**FUNs)
	
when_Ltot_is_5_and_05([1.181E-5, 5.054E-6],[-4.49E-6, 7.511E-6],
					  atotup1=A._atotup1, atotlow1=A._atotlow1)
when_Ltot_is_5_and_05([1.335E-5, 3.522E-6],[0.0     , 1.695E-6],
					  atotup2=A._atotup2, atotlow2=A._atotlow2)

when_Ltot_is_5_and_05([1.687E-5],[1.695E-6],atot=A.atot)

ltot=arange(0,15,0.01)

pltFunFromX(ltot,A.Atot,Nabase,1,'r')
pltFunFromX(ltot,A.DV.Lcrit,Nabase,1,'b:')
plt.show()
