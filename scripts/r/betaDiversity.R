args = commandArgs(TRUE)
mydata = read.csv(file=args[1], row.names=1, skip=1)
braycurtis = function(dat) {
	results = vector()
	for(j in 1:(ncol(dat)-1)) {
		x = j + 1
		for(i in x:ncol(dat)) {
			myfoo = dat[,c(j,i)]
			s_a = sum(myfoo[,1])
			s_b = sum(myfoo[,2])
			mysum = sum(apply(myfoo, 1, FUN = function(x) {min(x)}))
			bc = 1-(2*(mysum/(s_a+s_b)))
			results = append(results, bc)
		}
	}
	return(results)
}
results = braycurtis(mydata)
bp = boxplot(results, plot=FALSE)
cat(bp$stats,sep=',')
cat('\n')
cat(bp$out,sep=',')
cat('\n')
