source("cfg.r")
source("openVariables.r")
graphics.off()

experimentIDs   = colnames(ExperiementInfo)
varIDs          = c("leafAl","woodAl","rootAl")
ylab            = 'Allocation Fraction'

snameCfg        = "plotAllocationCfg"

plotBasicAnnualTS(experimentIDs,varIDs,ylab)

plotBasicSeasonaTS(experimentIDs,varIDs,ylab)