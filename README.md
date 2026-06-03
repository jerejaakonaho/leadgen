# PRH Lead Generator

This tool processes and filters open bulk data provided by the Finnish Patent and Registration Office (PRH). It allows you to search for business leads and export them to a CSV file.

## Features
* Streamed filtering of large JSON files to keep memory usage low.
* Filter companies by city, industry code, and website presence.
* A C pre-processing script to remove housing and real estate companies from the dataset.

## Setup

1. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Download the bulk JSON data from PRH's open data service and extract it to this directory (e.g., `data_20260603.json`).

## Usage

### 1. Pre-processing (Removing Housing Companies)
Run the C program first to remove housing and real estate companies from the bulk data. This reduces the file size and speeds up the Python script.

Compile and run the C program:
```bash
gcc -O3 remove_housing.c -o remove_housing_bin
./remove_housing_bin
```
This script reads the original `data_20260603.json` file and replaces it with a filtered version.

### 2. Lead Generation
Use the Python script to search for leads in the pre-processed data:

```bash
python lead_generator.py -c "Helsinki" -w -l 100
```

The command above finds the first 100 companies located in Helsinki that have a website, and saves them to `leads.csv`.

**Available parameters:**
* `-c, --city`: Filter by city (e.g., Tampere)
* `-i, --industry`: Filter by industry code (e.g., 62010)
* `-w, --require-website`: Only include companies that have a website
* `-nw, --no-website`: Only include companies that do not have a website
* `-eh, --exclude-housing`: Exclude housing/real estate companies (not needed if you ran the C script)
* `-l, --limit`: Limit the number of results (e.g., 500)
* `-d, --data`: Path to the data file (default: `data_20260603.json`)
* `-o, --output`: Output file name (default: `leads.csv`)
