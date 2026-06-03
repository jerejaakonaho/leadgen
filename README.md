# PRH Lead Generator

This tool is designed to process and filter open bulk data provided by the Finnish Patent and Registration Office (PRH). It allows you to search for potential business leads and conveniently export them to a CSV file.

## Features
* Memory-efficient (RAM-friendly) filtering of massive (over 1 GB) JSON files.
* Filter companies by city, industry code, and website presence.
* A high-performance C pre-processing script to quickly remove housing and real estate companies from the dataset.

## Setup

1. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Download the latest bulk JSON data from PRH's open data service and extract it to this directory (e.g., `data_20260603.json`).

## Usage

### 1. Pre-processing (Removing Housing Companies)
It is highly recommended to run the lightning-fast C program first. It removes all housing and real estate companies from the bulk data, drastically speeding up the Python script and saving a massive amount of RAM.

Compile and run the C program:
```bash
gcc -O3 remove_housing.c -o remove_housing_bin
./remove_housing_bin
```
This script reads the original `data_20260603.json` file and replaces it with a clean version.

### 2. Lead Generation
Use the Python script to search for leads in the pre-processed data:

```bash
python lead_generator.py -c "Helsinki" -w -l 100
```

The command above finds the first 100 companies located in Helsinki that have a website, and saves them to the `leads.csv` file.

**All available parameters:**
* `-c, --city`: Filter by city (e.g., Tampere)
* `-i, --industry`: Filter by industry code (e.g., 62010)
* `-w, --require-website`: Only include companies that HAVE a website
* `-nw, --no-website`: Only include companies that DO NOT HAVE a website
* `-eh, --exclude-housing`: Exclude housing/real estate companies (not needed if you ran the C script)
* `-l, --limit`: Limit the number of results (e.g., 500)
* `-d, --data`: Path to the data file (default: `data_20260603.json`)
* `-o, --output`: Output file name (default: `leads.csv`)
