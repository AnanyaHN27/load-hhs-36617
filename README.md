# Team Ephesus - Hospital Data Management

This repository contains scripts to manage and load hospital data into a PostgreSQL database. The project involves three main tables: `HospitalQualityDetails`, `HospitalSpecificDetails`, and `HospitalLogistics`. 

## Scripts Overview

There are three main scripts in this repository:

### 1. `create_tables.py`
This script creates the following three tables:

- **HospitalQualityDetails**  
  Stores hospital quality-related data.
  
- **HospitalSpecificDetails**  
  Contains detailed information about each hospital (address, name, etc.).
  
- **HospitalLogistics**  
  Includes logistics data for hospitals such as bed occupancy, ICU usage, and COVID-related stats.

This can be run like this:
```python
python create_tables.py
```

#### Table Schemas:

  - **HospitalQualityDetails**
  ```sql
  CREATE TABLE IF NOT EXISTS HospitalQualityDetails (
    hospital_pk TEXT REFERENCES HospitalSpecificDetails(hospital_pk),
    last_updated DATE CHECK (last_updated <= CURRENT_DATE),
    hospital_overall_rating INTEGER,
    hospital_ownership TEXT,
    emergency_services BOOLEAN,
    PRIMARY KEY (hospital_pk, last_updated)
  );
```
  - **HospitalSpecificDetails**
  ```sql
  CREATE TABLE IF NOT EXISTS HospitalSpecificDetails (
  hospital_pk TEXT PRIMARY KEY,
  state CHAR(2),
  hospital_name TEXT,
  address TEXT,
  city TEXT,
  zip CHAR(5),
  fips_code NUMERIC,
  longitude NUMERIC,
  latitude NUMERIC
);
```
  - **HospitalLogistics**
  ```sql
  CREATE TABLE IF NOT EXISTS HospitalLogistics (
  hospital_pk TEXT PRIMARY KEY REFERENCES HospitalSpecificDetails(hospital_pk),
  collection_week DATE CHECK (collection_week <= CURRENT_DATE::DATE),
  all_adult_hospital_beds_7_day_avg NUMERIC CHECK (all_adult_hospital_beds_7_day_avg >= 0),
  all_pediatric_inpatient_beds_7_day_avg NUMERIC CHECK (all_pediatric_inpatient_beds_7_day_avg >= 0),
  all_adult_hospital_inpatient_bed_occupied_7_day_avg NUMERIC CHECK (all_adult_hospital_inpatient_bed_occupied_7_day_avg >= 0),
  all_pediatric_inpatient_bed_occupied_7_day_avg NUMERIC CHECK (all_pediatric_inpatient_bed_occupied_7_day_avg >= 0),
  total_icu_beds_7_day_avg NUMERIC CHECK (total_icu_beds_7_day_avg >= 0),
  icu_beds_used_7_day_avg NUMERIC CHECK (icu_beds_used_7_day_avg >= 0),
  inpatient_beds_used_covid_7_day_avg NUMERIC CHECK (inpatient_beds_used_covid_7_day_avg >= 0),
  staffed_icu_adult_patients_confirmed_covid_7_day_avg NUMERIC CHECK (staffed_icu_adult_patients_confirmed_covid_7_day_avg >= 0)
  );
```
This script will need to be called first, to ensure that the tables exist for when data is loaded in with the next two scripts.

### 2. `load-hhs.py`
This script loads HHS (Hospital and Health Services) data into the `HospitalLogistics` table. It takes a single argument: the file path to the CSV file containing the HHS data.

This can be run like this:
  ```python
python load-hhs.py 2022-09-23-hhs-data.csv
```

### 3. `load-quality.py`
This script loads Hospital Quality data into the `HospitalQualityDetails` table. It takes two arguments: date for which the quality data is updated and the file path to the CSV file containing the quality data.


This can be run like this:
  ```python
python load-quality.py 2021-07-01 Hospital_General_Information-2021-07
```

### 4. `load_dashboard.sh`
This script runs the reporting dashboard using Streamlit. The dashboard visualizes the data loaded into the PostgreSQL database, allowing users to explore hospital logistics, quality metrics, and other key data points.

This can be run like this:
  ```bash
bash load_dashboard.sh
```

This script performs the following steps:

- Executes reporting_dashboard.py with Python to pre-check dependencies or prepare the environment.
- Launches the Streamlit dashboard using

Open the link provided by Streamlit in your browser to view the dashboard.

## Setup Instructions
1. Ensure that all dependencies are installed.
2. Create a file `credentials.py` with 2 variables: `DB_USER` and `DB_PASSWORD` and ensure these are set with your personal database credentials.
3. Run the `create-tables.py` script.
4. Run the `load-hhs.py` and `load-quality.py` scripts.
5. Launch the dashboard using the load_dashboard.sh script.

