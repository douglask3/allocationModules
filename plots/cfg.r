##########################################################################################
## Seup project and load packages                                                       ##
##########################################################################################
library("gitProjectExtras")
setupProjectStructure()
sourceAllLibs()

#library("libs/install_and_source_library.r")


##########################################################################################
## Variable Information                                                                 ##
##########################################################################################
## 
VarTitleInfo = rbind(
                #Name               #Units
    leadAl = c("Leaf Allocation"    , "%"),
    woodAl = c("Wood Allocation"    , "%"),
    rootAl = c("Root Allocation"    , "%"))
    
 
VarConstruction = list(
    leafAl = c(100   , match.fun("*"), "GL" , match.fun("/"), "NPP" ),
    woodAl = c(100   , match.fun("*"), "GW" , match.fun("/"), "NPP" ),
    rootAl = c(100   , match.fun("*"), "GR" , match.fun("/"), "NPP" ),
    YEAR   = c("DOY" , match.fun("/"), 365  , match.fun("+"), 'YEAR'))

#PlottingInformat =

