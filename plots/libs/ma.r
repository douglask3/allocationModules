ma <- function(x,n=12,sides=1) filter(x,rep(1/n,n))

ma.min <- function(x,n=12) {
	y=x
	y[]=NaN
	for (i in 7:(length(x)-6)) y=min(x[(i-6):(i+6)])
	
	return(y)
}

find_moving_average <- function(x,y,n=12,na.rm=TRUE,...) {
	
	if (na.rm) y=gapfill(y)
	
	if (is.null(dim(y))) y=as.matrix(y)
	browser()
	y=apply(y,2,ma,n,...)
	
	ns=ceiling(n/2)-1
	ne=length(x)-floor(n/2)
	
	x=x[ns:ne]
	y=y[ns:ne,]
	
	return(list(unlist(x),y))
}

find_moving_average_raster <- function(x,y,nn=12,...) {
	
	z=sum(y[[1:nn]])
	for (i in 1:(nlayers(y)+1-nn))  z=addLayer(z,sum(y[[i:(nn+i-1)]]))
	
	ns=ceiling(nn/2)-1
	ne=length(x)-floor(nn/2)
	x=x[ns:ne]
	
	return(list(x,z))
}

gapfill <- function(y) {
    x=1:length(y)
    test=is.na(y)
    c(xout,yout):=approx(x[!test],y[!test],x[test])
    y[xout]=yout
    return(y)
}