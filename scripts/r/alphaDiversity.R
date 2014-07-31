args = commandArgs(TRUE)
mydata = read.csv(file=args[1], row.names=1)
simpson = function(data,type="inverse"){
	simpson.diversity<-numeric(ncol(data))
	for(j in 1:ncol(data)){
		N<-sum(data[,j])
		prop<-data[,j]/N
		prop2<-prop^2
		D<-sum(prop2)
		if(type=="inverse") (simp<-1/D)
		if(type=="complement") (simp<-1-D)
		simpson.diversity[j]<-simp
	}
	plot.number<-1:ncol(data)
	return(rbind(plot.number,simpson.diversity))
}

results = simpson(t(mydata))
bp = boxplot(results[2,], plot=FALSE)
cat(bp$stats,sep=',')
cat('\n')
cat(bp$out,sep=',')
cat('\n')
