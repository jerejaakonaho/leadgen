#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

#define CHUNK_SIZE 1048576 // 1MB buffer for reading

const char* terms[] = {
    "asunto oy", "asunto-osakeyhti\xc3\xb6", "kiinteist\xc3\xb6 oy", "kiinteist\xc3\xb6osakeyhti\xc3\xb6", 
    "as.oy", "as. oy", "asunto-oy"
};
const int num_terms = 7;

// Function to convert string to lowercase for case-insensitive comparison
void to_lowercase(char* str) {
    for (int i = 0; str[i]; i++) {
        str[i] = tolower((unsigned char)str[i]);
    }
}

// Function to check if a string contains any of the housing terms
bool is_housing(const char* company_json) {
    // Check for industry code 682
    if (strstr(company_json, "\"mainBusinessLine\":{\"type\":\"682")) {
        return true;
    }
    
    // We only need to check the first part of the JSON where the names are usually located
    // but to be safe we can search the whole object (it's small)
    char* lower_json = strdup(company_json);
    if (!lower_json) return false;
    
    to_lowercase(lower_json);
    
    bool found = false;
    for (int i = 0; i < num_terms; i++) {
        if (strstr(lower_json, terms[i])) {
            found = true;
            break;
        }
    }
    
    free(lower_json);
    return found;
}

int main() {
    printf("Starting RAM-friendly filtering (C language)...\n");
    
    FILE *in = fopen("data_20260603.json", "rb");
    if (!in) {
        perror("Error opening input file");
        return 1;
    }
    
    FILE *out = fopen("data_20260603_tmp.json", "wb");
    if (!out) {
        perror("Error opening output file");
        fclose(in);
        return 1;
    }
    
    fputs("[\n", out);
    
    // Dynamic buffer for a single company object
    size_t obj_capacity = 1024 * 1024; // 1MB should be enough for one company
    char *obj_buffer = malloc(obj_capacity);
    if (!obj_buffer) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }
    
    size_t obj_len = 0;
    int depth = 0;
    bool in_string = false;
    bool escape = false;
    
    char read_buf[CHUNK_SIZE];
    size_t bytes_read;
    
    long long processed = 0;
    long long removed = 0;
    bool first = true;
    
    while ((bytes_read = fread(read_buf, 1, CHUNK_SIZE, in)) > 0) {
        for (size_t i = 0; i < bytes_read; i++) {
            char c = read_buf[i];
            
            if (depth == 0) {
                if (c == '{') {
                    depth = 1;
                    obj_buffer[0] = '{';
                    obj_len = 1;
                }
                continue;
            }
            
            // We are inside an object
            if (obj_len >= obj_capacity - 1) {
                obj_capacity *= 2;
                char *new_buf = realloc(obj_buffer, obj_capacity);
                if (!new_buf) {
        fprintf(stderr, "Memory reallocation failed\n");
        return 1;
    }
                obj_buffer = new_buf;
            }
            
            obj_buffer[obj_len++] = c;
            
            if (!escape && c == '"') {
                in_string = !in_string;
            }
            
            if (!in_string) {
                if (c == '{') depth++;
                else if (c == '}') depth--;
            }
            
            escape = (c == '\\' && !escape);
            
            if (depth == 0) {
                // Object complete
                obj_buffer[obj_len] = '\0';
                
                processed++;
                if (processed % 100000 == 0) {
                    printf("Processed %lld companies, removed housing/real estate companies so far: %lld...\n", processed, removed);
                }
                
                if (is_housing(obj_buffer)) {
                    removed++;
                } else {
                    if (!first) {
                        fputs(",\n", out);
                    }
                    first = false;
                    fputs(obj_buffer, out);
                }
                
                // Reset for next object
                obj_len = 0;
            }
        }
    }
    
    fputs("\n]\n", out);
    
    free(obj_buffer);
    fclose(in);
    fclose(out);
    
    printf("\nFiltering complete!\n");
    printf("Total processed: %lld companies.\n", processed);
    printf("Total removed: %lld housing/real estate companies.\n", removed);
    printf("Replacing original file...\n");
    
    if (rename("data_20260603_tmp.json", "data_20260603.json") != 0) {
        perror("Error replacing file");
        return 1;
    }
    
    printf("File replaced successfully!\n");
    return 0;
}
