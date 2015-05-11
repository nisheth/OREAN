clusterSamples = function (profiledata, metadata, filename) {
	require('ggplot2')
	require('gridExtra')
	require('reshape2')
	require('ggdendro')
	require('vegan')
	#save(profiledata, file='/home/mira/profile.rda')
	#save(metadata, file='/home/mira/metadata.rda')
	mymatrix = dcast(profiledata, samples~entity, value.var='profile', fill=0)
	row.names(mymatrix) = mymatrix$samples
	mymatrix$samples = NULL
	#save(mymatrix, file='/home/mira/profilematrix.rda')
	d = vegdist(mymatrix)
	#save(d, file='/home/mira/distancematrx.rda')
	#write.csv(as.matrix(d), file='/home/mira/debugging.txt')
	hc = hclust(d)
	# Setup data for colored bars
	df2<-data.frame(samples=factor(hc$labels,levels=hc$labels[hc$order]))
	mergedf2 = merge(df2, metadata, by.x="samples", by.y="samples", sort=F)	
	p1<-ggdendrogram(hc, rotate=FALSE)+
		theme(axis.text.x=element_blank(),
		      plot.margin=unit(c(1,1,-0.5,1),"cm") 
		     )			 
	p2<-ggplot(mergedf2,aes_string("samples",y="1",fill=colnames(mergedf2)[2]))+geom_tile()+
		scale_y_continuous(expand=c(0,0))+
		theme(axis.title=element_blank(),
		      axis.ticks=element_blank(),
	              axis.text=element_blank(),
	              legend.position="bottom",
	              plot.margin=unit(c(-1,1,0,1),"cm") 
	             )+
		guides(fill = guide_legend(nrow = 2))

	gp1<-ggplotGrob(p1)
	gp2<-ggplotGrob(p2)  	
	maxWidth = grid::unit.pmax(gp1$widths[2:5], gp2$widths[2:5])
	gp1$widths[2:5] <- as.list(maxWidth)
	gp2$widths[2:5] <- as.list(maxWidth)	
	pdf(filename, width=24, height=12, compress=F)
	grid.arrange(gp1, gp2, ncol=1, heights=c(9/10,1/10))
	dev.off()	
}
