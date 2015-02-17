source("cfg.r")

openFiles <- function(modelIDs,experimentIDs,varIDs) {
    fname1    = ModelInfo['filename',modelIDs]
    fname2    = ExperimentInfo[experimentIDs]
    dat       = lapply(fname1,openVariables,fname2,c("YEAR",varIDs))
}

openVariables <- function(fname1,fname2,varIDs,...) {
    filenames = paste(fname1,fname2,sep="")
    
    openFile <- function(filename) lapply(varIDs,reopenVariable,filename,...)
    
    lapply(filenames,openFile)
}

reopenVariable <- function(varID,filenameIn,...) {
    filename=paste(out_dir,'/',varID,"-",filenameIn,sep="")
    
    if (file.exists(filename)) var=read.csv(filename)[[1]]
        else {
            var=openVariable(varID,filenameIn,...)
            write.csv(var,filename,row.names=FALSE)
        }
    return(var)
}

openVariable <- function(varID,filename,inData=TRUE) {
    dat=read.csv(paste(data_dir,filename,sep='/'),skip=3, stringsAsFactors=FALSE)
    
    if (!any(names(VarConstruction)==varID)) {
        error("undefined variable")
        cat(varID)
    }
        
    constuction=VarConstruction[[varID]]
    
    var = sapply(constuction,is.character)
    constuction[var]=lapply(constuction[var],function(i) dat[i])
    
    nums= constuction[seq(1,length(constuction),by=2)]
    op  = c(match.fun('+'),constuction[seq(2,length(constuction),by=2)])
    
    out=0
    for (i in 1:length(nums)) out=op[[i]](out,nums[[i]])
    
    return(out[[1]])
}

## Example
#openVariables("D1GDAYEUCAMBAVG.csv","leafAl")