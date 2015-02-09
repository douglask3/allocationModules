plotBasicAnnualTS <- function(modelIDs,experimentIDs,varIDs,ylab) {
    setupBaiscAnnualTS(modelIDs,varIDs,"ANNUAL")
    
    c(dat,cols,ltys,titles):=openBasicAnnualTS(modelIDs,experimentIDs,varIDs)
    
    plotBasicAnnualTSVariables(dat,varIDs,cols,ltys,titles,ylab=ylab,xlab='Years')
    
    addBasicAnnualTSLegend(varIDs,experimentIDs,cols,ltys)
    addGitRev2plot.dev.off(paste(snameCfg,match.call.string(),sep="/"))
}


setupBaiscAnnualTS <- function(experimentIDs,varIDs,name) {
    name=paste(c("figs/",name,experimentIDs,varIDs,'.pdf'),collapse="-")
    
    pdf(name,height=3*(0.3+length(experimentIDs)),width=6)
    
    layoutMat=matrix(1:(length(experimentIDs)+1),length(experimentIDs)+1,1)
    layout(layoutMat,heights=c(rep(1,length(experimentIDs)),0.3))
    par(mar=c(2,2,1,0))
}

openBasicAnnualTS <- function(modelIDs,experimentIDs,varIDs) {
    dat     = openFiles(modelIDs,experimentIDs,varIDs)
    cols    = PlottingInformation['lineCol' ,varIDs]
    ltys    = PlottingInformation['lineType',experimentIDs]
    titles  = ModelInfo['Name',modelIDs]
    
    return(list(dat,cols,ltys,titles))
}

plotRange <- function(dat) 
    range(sapply(dat,function(i) sapply(i,function(j) range(unlist(j[-1]),na.rm=TRUE) )))

plotBasicAnnualTSVariables <- function (dat,varIDs,cols,ltys,titles,
                                        runningMean=365,...) {
    
    plotRange=plotRange(dat)

    plotVariables <- function(dat,title) {
        #c(title,plotNew)  := tail(dat,2)
        xRange=range(sapply(dat,function(i) range(i[1],na.rm=TRUE)))
        
        plot(xRange,plotRange,type='n',xaxt='n',...)
        
        plotVariable <- function(dat,lty) {
            git   = colnames(dat[[1]])
            x     = dat[[1]]
            y     = lapply(dat[-1],as.matrix)
    
            plotLines <- function(y,col,lty) {
                c(x,y):=find_moving_average(x,y,runningMean)
                lines(x,y,col=col,lty=as.numeric(lty))
            }
        
            mapply(plotLines,y,col=cols,lty=lty)
        }
        mapply(plotVariable,dat,ltys)
        mtext(title,side=3)
        #mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
    
    mapply(plotVariables,dat,titles)
    #apply(rbind(dat,titles,plotNew),2,)
    axis(side=1)
}

addBasicAnnualTSLegend <- function(varIDs,expermientIDs,cols,ltys) {
    grabInfo <- function(IDs) apply(VarTitleInfo[,IDs],2,paste,collapse=" ")
    legtitles1 = grabInfo(varIDs)
    legtitles2 = grabInfo(expermientIDs)
    legtitles  = paste(rep(legtitles1,each=length(experimentIDs)),rep(legtitles2,length(varIDs)))
    
    plot.new()
    legend(x='top',legend=legtitles,
           col=unlist(rep(cols,each=length(ltys))),
           lty=as.numeric(unlist(rep(ltys,each=length(cols))),horiz=TRUE))

}