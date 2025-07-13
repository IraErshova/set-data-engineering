import csv
import mysql.connector
from mysql.connector import Error
import argparse
import sys
import os

class DataInserter:
    def __init__(self, host: str = 'localhost', database: str = 'set_db',
                 user: str = 'set_user', password: str = 'set_password'):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
        self.csv_host_dir = './csv_data'  # for reading locally
        self.csv_container_dir = '/csv_files'  # for reading in docker
        self._connect_to_mysql()
        self.inserted_tables = set()

    def _connect_to_mysql(self):
        """connection to database"""
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_unicode=True,
                autocommit=False,
            )
            self.cursor = self.conn.cursor()
            print(f"Successfully connected to MySQL database: {self.database}")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def _get_csv_headers(self, file_name: str):
        host_path = os.path.join(self.csv_host_dir, file_name)
        with open(host_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)
            return '(' + ', '.join([h.strip() for h in headers]) + ')'

    def _load_data_infile(self, table_name: str, file_name: str):
        """Load data using LOAD DATA INFILE"""
        try:
            # get columns names
            columns_to_insert = self._get_csv_headers(file_name)
            container_path = os.path.join(self.csv_container_dir, file_name).replace('\\', '/')

            query = f"""
                    LOAD DATA INFILE '{container_path}'
                    INTO TABLE {table_name}
                    FIELDS TERMINATED BY ','
                    ENCLOSED BY '"'
                    LINES TERMINATED BY '\\n'
                    IGNORE 1 LINES
                    {columns_to_insert};
                """
            self.cursor.execute(query)
            self.conn.commit()
            self.inserted_tables.add(table_name)
            print(f"Loaded data into {table_name}")
        except Error as e:
            print(f"Error loading data into {table_name}: {e}")
            self.conn.rollback()
            raise

    def insert_advertisers(self, advertisers_file: str):
        """Insert advertisers from CSV file into the database"""
        print("Inserting advertisers")
        try:
            self._load_data_infile('advertisers', advertisers_file)
        except Exception as e:
            print(f"Error inserting advertisers: {e}")
            raise

    def insert_interests(self, interests_file: str):
        """Insert interests from CSV file into the database"""
        print("Inserting interests")
        try:
            self._load_data_infile('interests', interests_file)
        except Exception as e:
            print(f"Error inserting interests: {e}")
            raise

    def insert_countries(self, countries_file: str):
        """Insert countries from CSV file into the database"""
        print("Inserting countries")
        try:
            self._load_data_infile('countries', countries_file)
        except Exception as e:
            print(f"Error inserting countries: {e}")
            raise

    def insert_campaigns(self, campaigns_file: str):
        """Insert campaigns from CSV file into the database"""
        print("Inserting campaigns")
        try:
            self._load_data_infile('campaigns', campaigns_file)
        except Exception as e:
            print(f"Error inserting campaigns: {e}")
            raise

    def insert_users(self, users_file: str):
        """Insert users from CSV file into the database"""
        print("Inserting users")
        try:
            self._load_data_infile('users', users_file)
        except Exception as e:
            print(f"Error inserting users: {e}")
            raise

    def insert_impressions(self, impressions_file: str):
        """Insert ad impressions from CSV files into the database"""
        print("Inserting impressions")
        try:
            self._load_data_infile('ad_impressions', impressions_file)
        except Exception as e:
            print(f"Error inserting impressions: {e}")
            raise

    def insert_clicks(self, clicks_file: str):
        """Insert ad clicks from CSV files into the database"""
        print("Inserting clicks")
        try:
            self._load_data_infile('ad_clicks', clicks_file)
        except Exception as e:
            print(f"Error inserting clicks: {e}")
            raise

    def insert_user_interesets(self, user_interests_file: str):
        """Insert user interests from CSV file into the database"""
        print("Inserting user interests")
        try:
            self._load_data_infile('users_interests', user_interests_file)
        except Exception as e:
            print(f"Error inserting user interests: {e}")
            raise

    def rollback_all(self):
        """Rollback all inserted data"""
        if not self.inserted_tables:
            return

        print("Rolling back all inserted data")
        try:
            # Rollback in reverse order to handle foreign key constraints
            rollback_order = ['ad_clicks', 'ad_impressions', 'campaigns', 'advertisers', 'users']
            for table in rollback_order:
                if table in self.inserted_tables:
                    self.cursor.execute(f"DELETE FROM {table}")
                    self.cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1;")
                    print(f"Rolled back data from {table}")
            self.conn.commit()
            self.inserted_tables.clear()
            print("All data has been rolled back successfully")
        except Error as e:
            print(f"Error during rollback: {e}")
            self.conn.rollback()
            raise

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Insert data into MySQL database')

    parser.add_argument('--host', default='localhost', help='MySQL host (default: localhost)')
    parser.add_argument('--database', default='set_db', help='MySQL database name (default: set_db)')
    parser.add_argument('--user', default='set_user', help='MySQL user (default: set_user)')
    parser.add_argument('--password', default='set_password', help='MySQL password (default: set_password)')

    return parser.parse_args()


def insert_data():
    args = parse_args()
    inserter = DataInserter(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password
    )

    try:
        print("Starting data inserting process...")
        inserter.insert_interests('interests.csv')
        inserter.insert_countries('countries.csv')
        inserter.insert_users('users.csv')
        inserter.insert_advertisers('advertisers.csv')
        inserter.insert_campaigns('campaigns.csv')
        inserter.insert_impressions('ad_impressions.csv')
        inserter.insert_clicks('ad_clicks.csv')
        inserter.insert_user_interesets('users_interests.csv')

        print("Data inserting completed successfully!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        try:
            inserter.rollback_all()
        except Exception as rollback_error:
            print(f"Error during rollback: {rollback_error}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'inserter' in locals():
            inserter.close()
