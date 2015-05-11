heatmapDataCreator = function(profiledata, N=NULL) {
	require('reshape2')
	if (is.null(N) == F) {
		topentities = unique(profiledata[order(profiledata$profile, decreasing=T),]$entity)[1:N]
		profiledata = subset(profiledata, entity %in% topentities == T, drop=T)
		droplevels(profiledata)
	}
	mymatrix = dcast(profiledata, entity~samples, value.var='profile', fill=0)
	row.names(mymatrix) = mymatrix$entity
	mymatrix$entity = NULL
	#mymatrix.scaled = scale(mymatrix)
	hc.entity = hclust(dist(mymatrix))	
	hc.samples = hclust(dist(t(mymatrix)))	
	#finalMatrix = mymatrix.scaled[,hc.samples$order]
	finalMatrix = mymatrix[,hc.samples$order]
	finalMatrix = finalMatrix[hc.entity$order,]
	return(t(finalMatrix))
}
