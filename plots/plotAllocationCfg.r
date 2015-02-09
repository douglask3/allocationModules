source("cfg.r")
source("openVariables.r")
graphics.off()

modelIDs        = colnames(ModelInfo)
experimentIDs   = c('AMBVAR','ELEVAR')
varIDs          = c("leafAl","woodAl","rootAl")
ylab            = 'Allocation Fraction'

snameCfg        = "plotAllocationCfg"

plotStandard <- function(FUN) FUN(modelIDs,experimentIDs,varIDs,ylab)

plotStandard(plotBasicAnnualTS)
plotStandard(plotBasicSeasonalTS)