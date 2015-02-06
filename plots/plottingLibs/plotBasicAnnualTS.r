plotBasicAnnualTS <- function(experimentIDs,varIDs,ylab) {
    setupBaiscAnnualTS(experimentIDs,varIDs,"ANNUAL")
    
    c(dat,VarPlottingInfo,titles):=openBasicAnnualTS(experimentIDs,varIDs)
    
    plotBasicAnnualTSVariables(dat,varIDs,VarPlottingInfo,titles,ylab=ylab,xlab='Years')
    
    addBasicAnnualTSLegend(varIDs,VarPlottingInfo)
    addGitRev2plot.dev.off(paste(snameCfg,match.call.string(),sep="/"))
}


setupBaiscAnnualTS <- function(experimentIDs,varIDs,name) {
    name=paste(c("figs/",name,experimentIDs,varIDs,'.pdf'),collapse="-")
    
    pdf(name,height=3*(0.3+length(experimentIDs)),width=6)
    
    layoutMat=matrix(1:(length(experimentIDs)+1),length(experimentIDs)+1,1)
    layout(layoutMat,heights=c(rep(1,length(experimentIDs)),0.3))
    par(mar=c(2,2,1,0))
}

openBasicAnnualTS <- function(experimentIDs,varIDs) {
    filenames = ExperiementInfo['filename',experimentIDs]
    
    dat = sapply(filenames,openVariables,c("YEAR",varIDs))
    VarPlottingInfo= PlottingInformation[,varIDs]
    
    titles=ExperiementInfo['Name',experimentIDs]
    return(list(dat,VarPlottingInfo,titles))
}

plotRange <- function(dat) range(sapply(dat[-1,],range,na.rm=TRUE))

plotBasicAnnualTSVariables <- function (dat,varIDs,VarPlottingInfo,titles,
                                        runningMean=365,...) {
    
    plotRange=plotRange(dat)

    plotVariable <- function(dat,title) {
        title = tail(dat,1)
        dat   = head(dat,-1)
        git   = colnames(dat[[1]])
        x     = dat[[1]]
        #browser()
        y     = lapply(dat[-1],as.matrix)
        
        plot(range(dat[[1]]),plotRange,type='n',xaxt='n',...)
    
        plotLines <- function(y,col,lty) {
            c(x,y):=find_moving_average(x,y,runningMean)
            lines(x,y,col=col,lty=lty)
        }
    
        mapply(plotLines,y,col=VarPlottingInfo['lineCol',],
               lty=as.numeric(VarPlottingInfo['lineType',]))
        
        
        mtext(title,side=3)
        mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
   
    apply(rbind(dat,titles),2,plotVariable)
    axis(side=1)
}

addBasicAnnualTSLegend <- function(varIDs,PlottingInfo) {
    legtits=apply(VarTitleInfo[,varIDs],2,paste,collapse=" ")
    
    plot.new()
    legend(x='top',legend=legtits,
           col=as.character(PlottingInfo['lineCol',]),
           lty=as.numeric(PlottingInfo['lineType',]),horiz=TRUE)

}