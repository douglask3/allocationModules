source("cfg.r")
source("openVariables.r")
graphics.off()

filenames   = c("D1GDAYEUCAMBAVG.csv","D1GDAYEUCAMBAVG.csv")
varIDs      = c("leafAl","woodAl","rootAl")

ylab        = 'Allocation Fraction'

plotBasicTS <- function(filenames,varIDs,ylab) {
    setupBaiscTS(filenames)
    c(dat,PlottingInfo):=openBasicTS(filenames,varIDs)
    
    plotBasicTSVariables(dat,varIDs,ylab)
    
    addBasicTSLegend(varIDs)
}

setupBaiscTS <- function(filenames) {
    layoutMat=matrix(1:(length(filenames)+1),length(filenames)+1,1)
    layout(layoutMat,heights=c(rep(1,length(filenames)),0.3))
}

openBasicTS <- function(filenames,varIDs) {
    dat = sapply(filenames,openVariables,c("YEAR",varIDs))
    PlottingInfo= PlottingInformation[,varIDs]
    return(list(dat,PlottingInfo))
}

plotBasicTSVariables <- function (dat,varIDs,ylab) {
    
    plotRange=range(sapply(dat[-1,],range,na.rm=TRUE))

    plotVariable <- function(dat) {
        plot(range(dat[[1]]),plotRange,type='n',xlab='year',ylab=ylab)
    
        plotLines <- function(y,col,lty)
            lines(dat[[1]],y,col=col,lty=lty)
        
    
        mapply(plotLines,dat[-1],col=PlottingInfo['lineCol',],lty=as.numeric(PlottingInfo['lineType',]))
    }

    apply(dat,2,plotVariable)
}

addBasicTSLegend <- function(varIDs) {

    browser()

}


plotBasicTS(filenames,varIDs,ylab)