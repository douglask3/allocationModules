##########################################################################################
## Seup project and load packages                                                       ##
##########################################################################################
library("gitProjectExtras")
setupProjectStructure()
sourceAllLibs()
sourceAllLibs("plottingLibs")
options(stringsAsFactors = FALSE)

midmonth    = c(15,46,74,105,135,166,196,227,258,288,319,349)
mnthNames   = c('J','F','M','A','M','J','J','A','S','O','N','D') 

#library("libs/install_and_source_library.r")

##########################################################################################
## Variable Information                                                                 ##
##########################################################################################
filenames   = c("D1GDAYEUCAMBAVG.csv","D1GDAYEUCAMBAVG.csv")

ExperiementInfo = data.frame(
    row.names   = c('Name'          ,'filename'),
    control     = c("Control"       , "D1GDAYEUCAMBAVG.csv"),
    maxGPP      = c("Maximise GPP"  , "D1GDAYEUCAMBAVG.csv"))

##########################################################################################
## Variable Information                                                                 ##
##########################################################################################
## 
VarTitleInfo = data.frame(
    row.names   = c('Name'               ,'Units'),
    leafAl      = c("Leaf Allocation"    , "%"),
    woodAl      = c("Wood Allocation"    , "%"),
    rootAl      = c("Root Allocation"    , "%"))
    
 
VarConstruction = list(
    leafAl      = c(100   , match.fun("*"), "GL" , match.fun("/"), "NPP" ),
    woodAl      = c(100   , match.fun("*"), "GW" , match.fun("/"), "NPP" ),
    rootAl      = c(100   , match.fun("*"), "GR" , match.fun("/"), "NPP" ),
    YEAR        = c("DOY" , match.fun("/"), 365  , match.fun("+"), 'YEAR'))

PlottingInformation = data.frame (
    row.names   =  c("lineCol"        ,"lineType"),
    leafAl      =  c("green"          ,1),
    woodAl      =  c("brown"          ,1),
    rootAl      =  c("blue"           ,1))

