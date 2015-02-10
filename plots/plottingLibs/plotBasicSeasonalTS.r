plotBasicSeasonalTS <- function(modelIDs,experimentIDs,varIDs,ylab) {
    setupBaiscAnnualTS(modelIDs,experimentIDs,varIDs,"SEASONAL",oma=c(1,4,1,2))
    
    c(dat,cols,ltys,titles):=openBasicAnnualTS(modelIDs,experimentIDs,varIDs)
    
    dat=lapply(dat,function(i) lapply(i,makeSeasonal))
    
    plotBasicSeasolTSVariables(dat,varIDs,cols,titles,ylab=ylab,xlab=' ')
    
    plot.new()
    addGitRev2plot.dev.off(paste(snameCfg,match.call.string(),sep="/"))
}

plotBasicSeasolTSVariables <- function (dat,varIDs,cols,titles,...) {

    plotRange=plotRange(dat)
    
    plotVariable <- function(dat,xlab,ulab,axisT) {
        x     = dat[[1]]
        y     = lapply(dat[-1],as.matrix)
        
        plot(range(x),plotRange,type='n',xaxt='n',...)
       
        plotLines <- function(y,col) {
            for (i in 1:ceiling(nrow(y)/2)) {
                y1=y[i,]
                y2=y[nrow(y)-i+1,]
                polygon(c(x,rev(x)),c(y1,rev(y2)),border=NA,col=make.transparent(col,0.5))
            }
            lines(x,y[round(nrow(y)/2),],col=col)
        }
        
        mapply(plotLines,y,cols)
        
        mtext(xlab,side=2,line=3)
        mtext(ulab,side=3)
        if (axisT) axis(at=midmonth,labels=mnthNames,side=1)
        #mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
    
    mapply(function(i,j,axisT)
            mapply(plotVariable,i, xlab=c(j,rep('',length(i)-1)),ulab=experimentIDs,axisT)
        ,dat,titles,c(rep(FALSE,length(dat)-1),TRUE))
    
   
}

makeSeasonal <- function(dat,yrLength=365) {
    days=1:yrLength
    nyrs=floor(length(dat[[1]])/yrLength)
    
    convert2Seasonal <- function(dat) {
         x=sapply(1:yrLength,function(i) dat[seq(i,yrLength*nyrs,by=yrLength)])
         qs=apply(x,2,quantile,c(0.1,0.25,0.5,0.5,0.75,0.9),na.rm=TRUE)
    }
    
    out=lapply(dat[-1],convert2Seasonal)
    dat[-1]=matrix(out,length(dat)-1)

    dat[[1]]=1:365
    #for (i in 1:ncol(dat)) dat[1,i]=list(1:365)
    return(dat)
}