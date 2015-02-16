plotBasicAnnualTS <- function(modelIDs,experimentIDs,varIDs,ylab,ratios=NULL,ratioCols=NULL) {
    setupBaiscAnnualTS(modelIDs,NULL,ratios,varIDs,"ANNUAL")
    
    c(dat,cols,ltys,titles):=openBasicAnnualTS(modelIDs,experimentIDs,varIDs)
    
    if (!is.null(ratios)) {
        rids=sapply(ratios, function(i) which(experimentIDs==i))
        for (i in 1:length(dat)) for (j in 2:length(dat[[i]][[1]]))
            dat[[i]][[1]][[j]]=dat[[i]][[rids[1]]][[j]]/dat[[i]][[rids[2]]][[j]]
        
        cols=PlottingInformation['lineCol' ,modelIDs]
        plotOne=TRUE
    } else plotOne=FALSE
    
    plotBasicAnnualTSVariables(dat,varIDs,cols,ltys,
                               titles,ylab=ylab,xlab='Years',plotOne=plotOne)
    
    if (is.null(ratios)) addBasicAnnualTSLegend(varIDs,experimentIDs,cols,ltys)
        else addBasicAnnualTSLegend(modelIDs,NULL,cols,cex=0.67)
    addGitRev2plot.dev.off(paste(snameCfg,match.call.string(),sep="/"))
}


setupBaiscAnnualTS <- function(modelIDs,experimentIDs,ratios=NULL,varIDs,name,oma=c(1,1,1,2)) {
    name=paste(c("figs/",name,modelIDs,varIDs,'.pdf'),collapse="-")
    
    if (is.null(ratios)) nheight=length(modelIDs) else nheight=1
    if (!is.null(experimentIDs)) nwidth=length(experimentIDs) else nwidth=1
    
    pdf(name,height=3*(0.3+nheight),width=1+5*nwidth)
    
    layoutMat=matrix(1:(nheight*nwidth),nwidth,nheight)
    layoutMat=rbind(t(layoutMat),rep(nheight*nwidth+1,nwidth))
    layout(layoutMat,heights=c(rep(1,nheight),0.3))
    par(mar=c(2,2,1,0),oma=oma)
}

openBasicAnnualTS <- function(modelIDs,experimentIDs,varIDs) {
    dat     = openFiles(modelIDs,experimentIDs,varIDs)
    cols    = PlottingInformation['lineCol' ,varIDs]
    ltys    = PlottingInformation['lineType',experimentIDs]
    titles  = ModelInfo['Name',modelIDs]
    
    return(list(dat,cols,ltys,titles))
}

plotRange <- function(dat,plotOne=FALSE,runningMean=NULL) {
    
    range(sapply(dat,function(i) {
            if (plotOne) i=i[1]
            sapply(i,function(j) {
                if (!is.null(runningMean))
                    for (k in 2:length(j)) c(nn,j[[k]]):=find_moving_average(j[[1]],j[[k]],runningMean)
                range(unlist(j[-1]),na.rm=TRUE)
            })
        }))
        
 }       
        
plotBasicAnnualTSVariables <- function (dat,varIDs,cols,ltys,titles,
                                        runningMean=365,plotOne=FALSE,...) {
    plotRange=plotRange(dat,plotOne,runningMean)

    plotVariables <- function(dat,title,newPlot,...) {
        #c(title,plotNew)  := tail(dat,2)
        xRange=range(sapply(dat,function(i) range(i[1],na.rm=TRUE)))
        
        if (newPlot) plot(xRange,plotRange,type='n',xaxt='n',...)
        
        plotVariable <- function(dat,lty,col) {
            git   = colnames(dat[[1]])
            x     = dat[[1]]
            y     = lapply(dat[-1],as.matrix)
    
            plotLines <- function(y,col,lty) {
                c(x,y):=find_moving_average(x,y,runningMean)
                lines(x,y,col=col,lty=as.numeric(lty))
            }
            if (!is.na(col)) cols=col
            mapply(plotLines,y,col=cols,lty=lty)
        }
        
        if (plotOne) plotVariable(dat[[1]],ltys[[1]],...) else
            mapply(plotVariable,dat,ltys,...)
        if (!plotOne) mtext(title,side=3)
        #mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
    
    if (plotOne) mcol=cols else mcol=NaN
    mapply(plotVariables,dat,titles,c(TRUE,rep(!plotOne,length(dat)-1)),col=mcol)
    #apply(rbind(dat,titles,plotNew),2,)
    axis(side=1)
}

addBasicAnnualTSLegend <- function(varIDs,expermientIDs,cols,ltys=1,ncol=length(varIDs),cex=0.8) {
    grabInfo <- function(IDs) apply(VarTitleInfo[,IDs],2,paste,collapse=" ")
    legtitles1 = grabInfo(varIDs)
    if (is.null(expermientIDs)) legtitles2="" else legtitles2 = rev(grabInfo(expermientIDs))
    legtitles  = paste(rep(legtitles1,each=length(legtitles2)),rep(legtitles2,length(varIDs)))
    
    plot.new()
    legend(x='top',legend=legtitles,
           col=unlist(rep(cols,each=length(ltys))),
           lty=as.numeric(unlist(rep(ltys,length(cols)))),ncol=ncol,cex=cex)

}