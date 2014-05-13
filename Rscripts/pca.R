args <- commandArgs(TRUE)
filename <- args[1]

mydata <- read.table(filename,skip=1, sep=",")

ncolumns <- ncol(mydata)
mydata <- read.table(filename, header=TRUE, sep=",", colClasses = c(rep("character",2), rep("numeric",ncolumns - 2)))
if (sum(is.na(mydata[,ncol(mydata)])) == nrow(mydata)) {
  mydata <- mydata[,-c(ncol(mydata))]
}

mypca <- prcomp (t(mydata[,3:ncol(mydata)]), retx=TRUE)

write.csv(mypca$x[,1:2], quote=FALSE)
