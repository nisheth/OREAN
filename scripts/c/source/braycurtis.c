//
//  main.c
//  braycurtis
//
//  Created by Steven Bradley on 7/1/14.
//  Copyright (c) 2014 Steven Bradley. All rights reserved.
//

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int compare (const void * a, const void * b)
{
	float fa = *(float*) a;
	float fb = *(float*) b;
	return (fa > fb) - (fa < fb);
}

int main(int argc, const char * argv[])
{
	FILE *ptrFile;
	char buf[100000];
	const char *delim = ",";
	char *token;
    int rows = 0;
	int cols = 0;
    int lineNum = 0;
	if (argc < 2) {
		printf("Usage: ./braycurtis <file.txt>\n");
		return 1;
	}
	
	ptrFile = fopen(argv[1], "r");

    // Determine data size
	fgets(buf, 100000, ptrFile);
	if (buf[strlen(buf)] != '\0') {printf("Buffer exceeded\n"); return 1;}
	rows = atoi(strtok(buf, delim)); // rows count of the taxa
	cols = atoi(strtok(NULL, delim)); // columns count the samples
	
	// allocate array to hold the data
	float array[cols][rows];

	// loop through data and populate array
	while (fgets(buf, 100000, ptrFile)!=NULL) {
	
		token = strtok(buf, delim); // skip past taxa name
		token = strtok(NULL, delim);
		int count = 0;
		while (token != NULL) {
			array[count][lineNum] = atof(token);
			count++;
			token = strtok(NULL, delim);
		}
		lineNum++;
	}
	
	// compute bray curtis value for each comparision
        int myN = (cols*(cols+1)) / 2;
        float *results;
	results = malloc((myN+1) * sizeof *results);
	
	int N = 0;
	for (int i = 0; i < cols; i++) {
		for (int j = i+1; j < cols; j++) {
			int minSum = 0;
			int sA = 0;
			int sB = 0;
			for (int k = 0; k < rows; k++) {
				sA += array[i][k];
				sB += array[j][k];
				if (array[i][k] < array[j][k]) { minSum += array[i][k];}
				else {minSum+=array[j][k];}
			}
			results[N] = (float)(1-(2*((1.0*minSum)/(sA+sB))));
			N++;
		}
	}

	qsort(results, myN, sizeof(float), compare);

	int lc = (myN+1)*0.25;
	int med = (myN+1)*0.5;
	int uc = (myN+1)*0.75;
	float iqr = results[uc] - results[lc];
	float minthresh = results[lc] - iqr;
	float maxthresh = results[uc] + iqr;
	float *outliers;
	int outSize = 10;
	outliers = malloc(outSize*sizeof *array);
	int outCount = 0;
    int i = 0;
	float min = results[i];
	while (min < minthresh) {
		if (outCount == outSize) {
			outSize+=10;
			float *tmp = realloc(outliers, outSize * sizeof *outliers);
			if (tmp == NULL) { printf("Out of memory"); return 1; }
			outliers = tmp;
		}
		outliers[outCount] = min;
		outCount++;
		min = results[i];
		i++;
	}
	
	i = myN - 1;
	float max = results[i];
	while (max > maxthresh) {
		if (outCount == outSize) {
			outSize+=10;
			float *tmp = realloc(outliers, outSize * sizeof *outliers);
			if (tmp == NULL) { printf("Out of memory"); return 1; }
			outliers = tmp;
		}
		outliers[outCount] = max;
		outCount++;
		max = results[i];
		i--;
	}
	
	printf("%f,%f,%f,%f,%f\n", min, results[lc], results[med], results[uc], max);
	if (outCount > 0) {
		printf("%f", outliers[0]);
		for (i =1; i < outCount; i++) {
			printf(",%f", outliers[i]);
		}
	}
	free(outliers);
	free(results);
	printf("\n");
    return 0;
}

