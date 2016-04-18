# number of components to return
N = 5

args <- commandArgs(TRUE)
filename <- args[1]

mydata <- read.table(filename,skip=1, sep=",")

ncolumns <- ncol(mydata)
mydata <- read.table(filename, header=TRUE, sep=",", colClasses = c(rep("character",2), rep("numeric",ncolumns - 2)))
if (sum(is.na(mydata[,ncol(mydata)])) == nrow(mydata)) {
  mydata <- mydata[,-c(ncol(mydata))]
}

pcainput = t(mydata[,3:ncol(mydata)])
colnames(pcainput) = mydata$Taxa

mypca <- prcomp (pcainput, retx=TRUE)

# write pc1 and pc2 values for each sample
write.csv(mypca$x[,1:2], quote=FALSE)

# data separator
writeLines("-----")

# write variance composition
mysummary <- summary(mypca)
write.csv(format(t(mysummary$importance)[1:N,], digits=1), quote=FALSE)

# data separator
writeLines("-----")

# write the first N prinicpal components and the contribution
# to those N components by the N most impactful taxa
#write.csv(mypca$rotation[order(sapply(abs(mypca$rotation[,1]), sum), decreasing=T)[1:N],1:N], quote=F)
write.csv(format(mypca$rotation[order(rowSums(abs(mypca$rotation[,1:N])), decreasing=T)[1:N],1:N], digits=1), quote=F)
