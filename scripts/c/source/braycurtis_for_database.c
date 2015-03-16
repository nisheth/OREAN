//
//  main.c
//  betadiversity
//
//  Created by Steven Bradley on 10/15/14.
//  Copyright (c) 2014 VCUCSBC. All rights reserved.
//

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, const char * argv[]) {
    FILE * fp;                  // the file handle
    char * line = NULL;         // string holding current line
    size_t len = 0;             // size value
    ssize_t read;               // return value from getline
    int rows = 0;               // number of rows in the file
    int cols = 0;               // number of columns in the file
    char *token;                // stores the current string as we split the line
    int lineNum = 0;            // tracks which line is being processed
    const char *delim = ",";    // determines how file columns are split


    // open the file
    if (argc < 2) {
    	printf("Usage: ./braycurtis2 <file.txt>\n");
    	exit(EXIT_FAILURE);
    }

    fp = fopen(argv[1], "r");
    if (fp == NULL) { exit(EXIT_FAILURE); }
    
    // get file dimensions
    read = getline(&line, &len, fp);
    sscanf(line, "%d %d", &rows, &cols);

    // use file dimensions to set up variables
    float array[rows][cols];
    char * sample[rows];
    
    // loop through the data and populate the data array
    while ((read = getline(&line, &len, fp)) != -1) {
        token = strtok(line, delim);                    // sample name
        sample[lineNum] = malloc(strlen(token) + 1);    // allocate memory for string
        strcpy(sample[lineNum], token);                 // store sample name in array
        token = strtok(NULL, delim);                    // taxa abundance level
        int count = 0;                                  // count taxa
        while (token != NULL) {
            array[lineNum][count] = atof(token);        // convert string to float and store
            count++;                                    // count the occurrence
            token = strtok(NULL, delim);                // get next abundance value
        }
        lineNum++;                                      // count the line after processing
    }
    
    fclose(fp);
    
    int i = 0;
    int j = 0;
    int k = 0;
    for (i = 0; i < rows; i++) {                    // sample 'A' loop
        for (j = i+1; j < rows; j++) {              // sample 'B' loop
            float minSum = 0;
            float sA = 0;
            float sB = 0;
            for (k = 0; k < cols; k++) {            // loop through taxa for sample pair
                sA += array[i][k];
                sB += array[j][k];
                if (array[i][k] < array[j][k]) { minSum += array[i][k];}
                else {minSum+=array[j][k];}
            }
            float N = (1-(2*((1.0*minSum)/(sA+sB))));
            printf("%s\t%s\t%f\n", sample[i], sample[j], N); // report this diversity value
        }
    }

    exit(EXIT_SUCCESS);
}

