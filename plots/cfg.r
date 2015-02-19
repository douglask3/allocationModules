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
data_dir        = 	"~/Documents/allocationModules/runGday/EucFace/outputs/"

ModelInfo = data.frame(
    row.names   = c('Name'          ,'filename'),
    fixed       = c("Fixed"         , "D1GDAYEUCFIXED"),
    allometric  = c("Allometric"    , "D1GDAYEUCALLOMETRIC"),
    maxGPP      = c("Maximise GPP"  , "D1GDAYEUCMAXIMIZEGPP"),
    maxWOOD     = c("Maximise Wood" , "D1GDAYEUCMAXIMIZEWOOD"))

ExperimentInfo = c(AMBAVG="AMBAVG.csv",
                   AMBVAR="AMBVAR.csv",
                   ELEAVG="ELEAVG.csv",
                   ELEVAR="ELEVAR.csv")

##########################################################################################
## Variable Information                                                                 ##
##########################################################################################
## 
VarTitleInfo = data.frame(
    row.names   = c('Name'                ,'Units'),
    NPP         = c("NPP"                 , "gC/m2"),
    GPP         = c("GPP"                 , "gC/m2"),
    leafAl      = c("Leaf Allocation"     , "%"),
    woodAl      = c("Wood Allocation"     , "%"),
    rootAl      = c("Root Allocation"     , "%"),
    AMBAVG      = c("Ambient average CO2" ,  ""),
    ELEVAR      = c("Ambient CO2"         ,  ""),
    AMBAVG      = c("Elevated average CO2",  ""),
    AMBVAR      = c("Elevated CO2"        ,  ""),
    fixed       = c("Fixed"               ,  ""),
    allometric  = c("Allometric"          ,  ""),
    maxGPP      = c("Maximise GPP"        ,  ""),
    maxWOOD     = c("Maximise Wood"       ,  ""))
    
 
VarConstruction = list(
    NPP         = c(1, match.fun("*"),"NPP"),
    GPP         = c(1, match.fun("*"),"GPP"),
    leafAl      = c(100   , match.fun("*"), "GL" , match.fun("/"), "NPP" ),
    woodAl      = c(100   , match.fun("*"), "GW" , match.fun("/"), "NPP" ),
    rootAl      = c(100   , match.fun("*"), "GR" , match.fun("/"), "NPP" ),
    YEAR        = c("DOY" , match.fun("/"), 365  , match.fun("+"), 'YEAR'))

PlottingInformation = data.frame (
    row.names   =  c("lineCol"        ,"lineType"),
    NPP         =  c("purple"         ,1),
    GPP         =  c("forestgreen"    ,1),
    leafAl      =  c("green"          ,1),
    woodAl      =  c("brown"          ,1),
    rootAl      =  c("blue"           ,1),
    AMBAVG      =  c("transparent"    ,2),
    AMBVAR      =  c("transparent"    ,1),
    ELEAVG      =  c("transparent"    ,3),
    ELEVAR      =  c("transparent"    ,4),
    fixed       =  c("Black"          ,1),
    allometric  =  c("Red"            ,1),
    maxGPP      =  c("Blue"           ,1),
    maxWOOD     =  c("green"          ,1))

