source("cfg.r")
source("openVariables.r")
graphics.off()

experimentIDs   = c("control","maxGPP")
varIDs          = c("leafAl","woodAl","rootAl")
ylab            = 'Allocation Fraction'

plotBasicTS <- function(experimentIDs,varIDs,ylab) {
    setupBaiscTS(experimentIDs)
    c(dat,VarPlottingInfo,titles):=openBasicTS(experimentIDs,varIDs)
    
    plotBasicTSVariables(dat,varIDs,VarPlottingInfo,titles,ylab)
    
    addBasicTSLegend(varIDs,VarPlottingInfo)
}

setupBaiscTS <- function(experimentIDs) {
    layoutMat=matrix(1:(length(experimentIDs)+1),length(experimentIDs)+1,1)
    layout(layoutMat,heights=c(rep(1,length(experimentIDs)),0.7))
}

openBasicTS <- function(experimentIDs,varIDs) {
    filenames = ExperiementInfo['filename',experimentIDs]
    
    dat = sapply(filenames,openVariables,c("YEAR",varIDs))
    VarPlottingInfo= PlottingInformation[,varIDs]
    
    titles=ExperiementInfo['Name',experimentIDs]
    
    return(list(dat,VarPlottingInfo,titles))
}

plotBasicTSVariables <- function (dat,varIDs,VarPlottingInfo,titles,ylab,runningMean=365) {
    
    plotRange=range(sapply(dat[-1,],range,na.rm=TRUE))

    plotVariable <- function(dat,title) {
        title = tail(dat,1)
        dat   = head(dat,-1)
        plot(range(dat[[1]]),plotRange,type='n',xlab='year',ylab=ylab)
    
        plotLines <- function(y,col,lty) {
            browser()
            c(x,y):=find_moving_average(dat[[1]],y,runningMean)
            lines(x,y,col=col,lty=lty)
        }
    
        mapply(plotLines,dat[-1],col=VarPlottingInfo['lineCol',],
               lty=as.numeric(VarPlottingInfo['lineType',]))
        
        mtext(title,side=3)
    }
   
    apply(rbind(dat,titles),2,plotVariable)
}

addBasicTSLegend <- function(varIDs,PlottingInfo) {
    legtits=apply(VarTitleInfo[,varIDs],2,paste,collapse=" ")
    
    plot.new()
    legend(x='top',legend=legtits,
           col=as.character(PlottingInfo['lineCol',]),
           lty=as.numeric(PlottingInfo['lineType',]),horiz=TRUE)

}


plotBasicTS(experimentIDs,varIDs,ylab)