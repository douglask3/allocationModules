##########################################################################################
## Seup project and load packages                                                       ##
##########################################################################################
library("gitProjectExtras")
setupProjectStructure()
sourceAllLibs()
options(stringsAsFactors = FALSE)

#library("libs/install_and_source_library.r")


##########################################################################################
## Variable Information                                                                 ##
##########################################################################################
## 
VarTitleInfo = rbind(
                #Name               #Units
    leafAl = c("Leaf Allocation"    , "%"),
    woodAl = c("Wood Allocation"    , "%"),
    rootAl = c("Root Allocation"    , "%"))
    
 
VarConstruction = list(
    leafAl = c(100   , match.fun("*"), "GL" , match.fun("/"), "NPP" ),
    woodAl = c(100   , match.fun("*"), "GW" , match.fun("/"), "NPP" ),
    rootAl = c(100   , match.fun("*"), "GR" , match.fun("/"), "NPP" ),
    YEAR   = c("DOY" , match.fun("/"), 365  , match.fun("+"), 'YEAR'))

PlottingInformation = data.frame (
    row.names=c("lineCol"        ,"lineType"),
    leafAl =  c("green"          ,1),
    woodAl =  c("brown"          ,1),
    rootAl =  c("blue"           ,1))

