MaxW Tests
==========
This is a series of tests of the python-coded MaxW
allocation and supporting production functions. Code
run using the following parameters should match the 
Mcad file provided by Ross McMurtie. See docs/Info
for original file.

First off, this currently needs setting up (hopefully I can remove
this but of code soon:

```python
import re
import sys
import argparse

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.nbjson import JSONWriter

import IPython.nbformat.v3.nbbase as nbbase

def printNewLine(txt): print("\n"+txt+":\t")
```

Parameter values
----------------
As defined by Mcad file

```python
from math import pi

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
                        # i.e seconds per year
```

Photosynthesis Equations
------------------------

```python
from photosythesis import photosythesis
ph=photosythesis(An,N0,Kl,Rleaf,I0,alpha,Convfactor)

printNewLine("Asat when na=0.003")
print ph.Asat(0.003)

printNewLine("I0 when lai=0.0")
print ph.I(0.0)

printNewLine("Aa for lai=0.0 and na=0.003. Expect 0.516(ish)")
print ph.Aa(0.0,0.003)

printNewLine("aAdN when lai=0.0 and na=0.003")
print ph.dAdN(0.0,0.003)
```

Solution derived by Lagrange multiplier method
---------------------------------------------
```python
from dimensionless_variables import dimensionless_variables

printNewLine("Dimensionless variables when nabase=Nabase from paramter list and ltot=5")
nabase=Nabase
ltot=5.0

var=dimensionless_variables(An,alpha,Kl,I0,N0)

printNewLine("Expect 0.336 for zeta")
print var.zeta(nabase)

printNewLine("Expect 2.977 for Lcrit0")
print var._Lcrit0(ltot, nabase)

printNewLine("Expect 2.977 for Lcrit")
print var.Lcrit(ltot, nabase)

printNewLine("Expect 3.597 for ExpKLcrit0 and ExpKLcrit")
print var._ExpKLcrit0(ltot, nabase)
print var.ExpKLcrit(ltot, nabase)


printNewLine("Dimensionless variables when nabase=Nabase from paramter list and ltot=0.5")
var=dimensionless_variables(An,alpha,Kl,I0,N0)
nabase=Nabase
ltot=0.5

printNewLine("Expect -0.139 for Lcrit0")
print var._Lcrit0(ltot, nabase)

printNewLine("Expect 0 for Lcrit")
print var.Lcrit(ltot, nabase)

printNewLine("Expect 1 for ExpKLcrit")
print var.ExpKLcrit(ltot, nabase)

```

N balance
----------




Determine Utot (kg N/m2/y) from Rtot (kg C/m2/y):
-------------------------------------------------


Vertical profiles of leaf N content (Na(L), kg N/m2), photosynthesis (Aa(L), kg C/m2/s), leaf C payback (Xc, kg C/m2), leaf C export per unit N investment (ef, kg C / kg N):
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------



