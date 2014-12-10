plotBasicSeasonaTS <- function(experimentIDs,varIDs,ylab) {
    setupBaiscAnnualTS(experimentIDs)
    
    c(dat,VarPlottingInfo,titles):=openBasicAnnualTS(experimentIDs,varIDs)
    dat=makeSeasonal(dat)
    
    plotBasicSeasolTSVariables(dat,varIDs,VarPlottingInfo,titles,ylab=ylab,xlab=' ')
    
}

plotBasicSeasolTSVariables <- function (dat,varIDs,VarPlottingInfo,titles,...) {

    plotRange=plotRange(dat)
    
    plotVariable <- function(dat,title) {
        title = tail(dat,1)[[1]]
        dat   = head(dat,-1)
        x     = dat[[1]]
        y     = lapply(dat[-1],as.matrix)
        
        plot(range(x),plotRange,type='n',xaxt='n',...)
        axis(at=midmonth,labels=mnthNames,side=1)
    
        plotLines <- function(y,col,lty) {
            for (i in 1:ceiling(nrow(y)/2)) {
                y1=y[i,]
                y2=y[nrow(y)-i+1,]
                polygon(c(x,rev(x)),c(y1,rev(y2)),border=NA,col=make.transparent(col,0.5))
            }
            lines(x,y[round(nrow(y)/2),],col=col,lty=lty)
        }
    
        mapply(plotLines,y,col=VarPlottingInfo['lineCol',],
               lty=as.numeric(VarPlottingInfo['lineType',]))
        
        mtext(title,side=3)
        #mtext(git,side=1,cex=0.33,adj=0.98,line=-2,col="#00000066")
    }
   
    apply(rbind(dat,titles),2,plotVariable)


}



makeSeasonal <- function(dat,yrLength=365) {
    days=1:yrLength
    nyrs=floor(length(dat[[1]][[1]])/yrLength)
   
    
    convert2Seasonal <- function(dat) {
         x=sapply(1:yrLength,function(i) dat[[1]][seq(i,yrLength*nyrs,by=yrLength)])
         qs=apply(x,2,quantile,c(0,0.25,0.5,0.75,1),na.rm=TRUE)
    }
    
    out=lapply(dat[-1,],convert2Seasonal)
    dat[-1,]=matrix(out,nrow(dat[-1,]))
    for (i in 1:2) dat[1,i]=list(1:365)
    return(dat)
}