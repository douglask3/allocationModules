source("cfg.r")
source("openVariables.r")
graphics.off()

modelIDs        = colnames(ModelInfo)
experimentIDs   = c('AMBVAR','ELEVAR')
ylab            = 'Allocation Fraction (%)'

snameCfg        = "plotAllocationCfg"

plotAll <- function(varIDs,...) {
    plotStandard <- function(FUN,varIDs) FUN(modelIDs,experimentIDs,varIDs,ylab,...)

    plotStandard(plotBasicAnnualTS,varIDs)
    plotStandard(plotBasicSeasonalTS,varIDs)
}

plotAll(c("leafAl","woodAl","rootAl"))
plotAll(c("NPP","GPP"))
plotAll(c("NPP"),ratios=c("ELEVAR","AMBVAR"))