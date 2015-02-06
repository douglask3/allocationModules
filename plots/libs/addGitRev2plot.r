addGitRev2plot <- function(additional=NULL) {

    revNo=returnGitVersionNumber()
    revURL=returnGitRemoteURL()
    
    mtestStandard <- function(x,...) mtext(x,side=1,adj=1,cex=0.33,col="#00000077",...)
    mtestStandard(paste(revURL,revNo,sep=": "),line=-1)
    
    if (!is.null(additional)) mtestStandard(additional)
}

addGitRev2plot.dev.off <- function(...) {
    addGitRev2plot(...)
    dev.off()
}