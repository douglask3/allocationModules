source("cfg.r")
source("openVariables.r")
graphics.off()

modelIDs        = colnames(ModelInfo)
experimentIDs   = c('AMBVAR','ELEVAR')

snameCfg        = "plotAllocationCfg"

plotAll <- function(varIDs,...) {
    plotStandard <- function(FUN,varIDs) FUN(modelIDs,experimentIDs,varIDs,ylab,...)

    plotStandard(plotBasicAnnualTS,varIDs)
    plotStandard(plotBasicSeasonalTS,varIDs)
}


ylab  = "'Allocation Fraction (%)'"
plotAll(c("leafAl","woodAl","rootAl"))

ylab  = "'Production gC '*m^2*' d'^1"
plotAll(c("NPP","GPP"))

ylab  = "'ratio'"
plotAll(c("NPP"),ratios=c("ELEVAR","AMBVAR"))