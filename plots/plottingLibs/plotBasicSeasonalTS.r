plotBasicSeasonalTS <- function(modelIDs,experimentIDs,varIDs,ylab,ratios=NULL,ratioCols=NULL) {
    setupBaiscAnnualTS(modelIDs,experimentIDs,ratios,varIDs,"SEASONAL",oma=c(1,4,1,2))
    
    c(dat,cols,ltys,titles,plotOne):=openBasicAnnualTS(modelIDs,experimentIDs,varIDs,ratios)
    
    dat=lapply(dat,function(i) lapply(i,makeSeasonal))
    
    plotBasicSeasolTSVariables(dat,varIDs,cols,titles,ylab=ylab,xlab=' ',plotOne)
    
    plot.new()
    addGitRev2plot.dev.off(paste(snameCfg,"plotBasicSeasonalTS",sep="/"))
}

plotBasicSeasolTSVariables <- function (dat,varIDs,cols,titles,plotOne,...) {

    plotRange=plotRange(dat)
    
    plotVariable <- function(dat,plotT,xlab,ulab,axisT,colss=cols) {
        x     = dat[[1]]
        y     = lapply(dat[-1],as.matrix)
        
        if (plotT) plot(range(x),plotRange,type='n',xaxt='n',...)
       
        plotLines <- function(y,col) {
            for (i in 1:ceiling(nrow(y)/2)) {
                y1=y[i,]
                y2=y[nrow(y)-i+1,]
                polygon(c(x,rev(x)),c(y1,rev(y2)),border=NA,col=make.transparent(col,0.9))
            }
            lines(x,y[round(nrow(y)/2),],col=col)
        }
        mapply(plotLines,y,colss)
        
        mtext(xlab,side=2,line=3)
        mtext(ulab,side=3)
        if (axisT) axis(at=midmonth,labels=mnthNames,side=1)
        
        #mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
    
    axisTest=c(rep(FALSE,length(dat)-1),TRUE)
    plotTest=c(TRUE,rep(FALSE,length(dat)-1))
    if (plotOne) {
        plotFun <- function(i,j,axisT,plotT,col) 
            plotVariable(i[[1]],plotT, xlab=j,ulab="",axisT,cols=col)
    } else {
        plotTest=TRUE
        plotFun <- function(i,j,axisT,...) 
            mapply(plotVariable,i,TRUE, xlab=c(j,rep('',length(i)-1)),ulab=experimentIDs,axisT)
    }
    
    mapply(plotFun,dat,titles,axisTest,plotTest,cols)
}

makeSeasonal <- function(dat,yrLength=365) {
    days=1:yrLength
    nyrs=floor(length(dat[[1]])/yrLength)
    
    convert2Seasonal <- function(dat) {
         x=sapply(1:yrLength,function(i) dat[seq(i,yrLength*nyrs,by=yrLength)])
         qs=apply(x,2,quantile,c(0.25,0.5,0.5,0.75),na.rm=TRUE)
    }
    
    out=lapply(dat[-1],convert2Seasonal)
    dat[-1]=matrix(out,length(dat)-1)

    dat[[1]]=1:365
    #for (i in 1:ncol(dat)) dat[1,i]=list(1:365)
    return(dat)
}