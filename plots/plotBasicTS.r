source("cfg.r")
source("openVariables.r")
graphics.off()

filenames   = c("D1GDAYEUCAMBAVG.csv","D1GDAYEUCAMBAVG.csv")
varIDs      = c("leafAl","woodAl","rootAl")

ylab        = 'Allocation Fraction'

layoutMat=matrix(1:(length(filenames)+1),length(filenames)+1,1)
layout(layoutMat,heights=c(rep(1,length(filenames)),0.3))
dat = sapply(filenames,openVariables,c("YEAR",varIDs))

plotRange=range(sapply(dat[-1,],range,na.rm=TRUE))

plotVariables <- function(dat) {
    
    plot(range(dat[[1]]),plotRange,type='n',xlab='year',ylab=ylab)
    
    plotLines <- function(y,...)
        lines(dat[[1]],y,...)
        
    mapply(plotLines,dat[-1])
    
}

apply(dat,2,plotVariables)

browser()