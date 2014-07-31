args = commandArgs(TRUE) 
filename = args[1]
dat = read.csv(filename, header=FALSE, row.names=1, quote="")
bp = boxplot(t(dat), plot=FALSE)
for(i in 1:ncol(bp$stats)) {
	cat(c(bp$names[i], bp$stats[,i], bp$out[bp$group  == i]), sep=',')
	cat("\n")
}
