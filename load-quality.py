import psycopg
import pandas as pd
import sys
import numpy as np
import credentials
from datetime import datetime
from psycopg import errors


def process_cms_data(data):
    """
    Processes and transformation CMS hospital quality data.

    Parameters:
    data (pd.DataFrame): The raw data to be preprocessed. 
    Expected columns include minimum of:
    ['Facility ID', 'State', 'Facility Name', 'Address', 'City', 'ZIP Code', 
     'Emergency Services', 'Hospital Ownership', 'Hospital overall rating', 
     'last_updated']

    Returns:
    pd.DataFrame: Processed and transformed CMS hospital quality data.

    Notes:
    - The function performs the following transformations:
      - Renames columns to match database schema.
      - Filters for valid hospital primary keys (6 characters).
      - Converts 'emergency_services' to a boolean (True if "Yes", False if "No").
      - Converts 'hospital_overall_rating' to an integer; replaces non-numeric
        values with NaN.
      - Selects only columns of interest for further steps.
      - Extracts longitude and latitude from 'geocoded_hospital_address'.
    """
    
    # list the columns to be used in preparing and loadking cms quality data
    columns = [
        "hospital_pk",
        "last_updated",
        "hospital_overall_rating",
        "hospital_name",
        "address",
        "city",
        "zip",
        "state",
        "hospital_ownership",
        "emergency_services",
    ]

    rename_columns = {
        'Facility ID': 'hospital_pk',
        'State': 'state',
        'Facility Name': 'hospital_name',
        'Address': 'address',
        'City': 'city',
        'ZIP Code': 'zip',
        'Emergency Services': 'emergency_services',
        'Hospital Ownership': 'hospital_ownership',
        'Hospital overall rating': 'hospital_overall_rating'
        }

    # rename columns to be consistent with the schema
    data = data.rename(columns=rename_columns)

    # data transformtions

    # ensure that we do not take any row with bizzare hospital_pk value
    data['valid_pk'] = data["hospital_pk"].\
        apply(lambda x: True if len(x) <= 6 else False)
    data = data[data['valid_pk']]

    # convert emergency_services is 'Yes'/'No', convert to boolean
    data['emergency_services'] = data['emergency_services'].\
        apply(lambda x: True if x.lower() == 'yes' else False)
    # hospital_overall_rating is in string, convert it to int
    data['hospital_overall_rating'] = data['hospital_overall_rating'].\
        apply(lambda x: int(x) if x.isnumeric() else np.nan)

    # take only columns of ineterest
    data = data[columns]

    print("CMS data processing complete")

    return data


def batch_insert_cms_data(conn, data, batch_size=100):
    """
    Inserts CMS hospital quality data into two database tables in batches,
    with handling for foreign key violations.

    Parameters:
    conn (psycopg.Connection): Database connection object.
    data (pd.DataFrame): Processed CMS hospital data to be inserted.
    batch_size (int): Number of records to process per batch. Default is 100.

    Notes:
    - The function performs the following transformations:
      - Defines SQL insertion queries for insertion.
      - Inserts rows in 'HospitalQualityDetails' table in batches.
      - Handles ForeignKeyViolation error by first inserting into 'HospitalSpecificDetails'
        if required, and then retries insertion into 'HospitalQualityDetails'.
      - Uses 'ON CONFLICT DO NOTHING' to prevent duplicate entries on conflict.
    """
    
    # Define the SQL query for insertion
    cur = conn.cursor()

    # define insert query for HospitalQualityDetails
    quality_insert_query = """
        INSERT INTO HospitalQualityDetails (
            hospital_pk, last_updated, hospital_overall_rating,
            hospital_ownership, emergency_services
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (hospital_pk, last_updated) DO NOTHING;
    """

    # define insert query for HospitalSpecificDetails
    static_insert_query = """
        INSERT INTO HospitalSpecificDetails (
            hospital_pk, hospital_name, address, city, zip, state
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (hospital_pk) DO NOTHING;
    """

    # insert rows in HospitalQualityDetails in batches
    for row_index in range(0, len(data), batch_size):
        batch_df = data[row_index:row_index + batch_size]
        print("Running process for batch", (row_index // batch_size) + 1)

        # Prepare values for insertion in HospitalQualityDetails
        quality_values = [
            (
                row['hospital_pk'],
                row['last_updated'],
                row['hospital_overall_rating'],
                row['hospital_ownership'],
                row['emergency_services']
                )
            for idx, row in batch_df.iterrows()
        ]
        try:
            with conn.transaction():
                cur.executemany(quality_insert_query, quality_values)
                print("Insertion successful for HospitalQualityDetails table")

        except errors.ForeignKeyViolation:
            # Handle foreign key violation by inserting
            # into HospitalSpecificDetails first
            print("Foreign key violation encountered")
            print("Inserting into HospitalSpecificDetails.")

            # Prepare values for insertion into HospitalSpecificDetails
            static_values = [
                (
                    row['hospital_pk'],
                    row['hospital_name'],
                    row['address'],
                    row['city'],
                    row['zip'],
                    row['state']
                    )
                for idx, row in batch_df.iterrows()
            ]
            # Insert into HospitalSpecificDetails to resolve FK dependency
            with conn.transaction():
                cur.executemany(static_insert_query, static_values)
                print("Insertion successful for HospitalSpecificDetails table")

            # Reinserting into HospitalQualityDetails after resolving FK error
            with conn.transaction():
                cur.executemany(quality_insert_query, quality_values)
                print("Insertion successful for HospitalQualityDetails")

        except Exception as e:
            print(f"Error in batch {(row_index // batch_size) + 1}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: load-quality.py <last_updated> <file_path> ")
        sys.exit(1)

    # Get file path and last_updated date from command-line arguments
    file_path = sys.argv[2]
    last_updated = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

    # last_updated = date(2021,7,1)
    # file_path = 'data/Hospital_General_Information-2021-07.csv'

    data = pd.read_csv(file_path)   
    # insert last_updated column in the data. We get it from sys.args
    data['last_updated'] = last_updated
    
    processed_data = process_cms_data(data)

    conn = psycopg.connect(
        host="pinniped.postgres.database.azure.com",
        dbname=credentials.DB_USER,
        user=credentials.DB_USER,
        password=credentials.DB_PASSWORD
    )

    batch_size = 100

    batch_insert_cms_data(conn, processed_data, batch_size)