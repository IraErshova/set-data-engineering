import csv
from datetime import datetime
import os
from tabulate import tabulate
import mysql.connector
from mysql.connector import Error
import argparse
import sys


class PerformanceReport:
    def __init__(self, host: str = 'localhost', database: str = 'set_db',
                 user: str = 'set_user', password: str = 'set_password'):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
        self.output_folder = 'reports'
        self._connect_to_mysql()

        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

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
            )
            self.cursor = self.conn.cursor()
            print(f"Successfully connected to MySQL database: {self.database}")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def execute_query_from_file(self, filename):
        # Create report file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"performance_report_{timestamp}.csv"
        csv_filepath = os.path.join(self.output_folder, csv_filename)

        with open(filename, 'r') as file:
            content = file.read()

            # Split by semicolon to get individual query blocks
            query_blocks = content.split(';')

            with open(csv_filepath, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)

                query_index = 1  # Used as fallback

                for block in query_blocks:
                    block = block.strip()
                    if not block:
                        continue

                    lines = block.split('\n')
                    comments = []
                    query_lines = []

                    for line in lines:
                        line = line.strip()
                        if line.startswith('--'):
                            comments.append(line.lstrip('--').strip())
                        elif line:
                            query_lines.append(line)

                    query = ' '.join(query_lines)
                    comment_text = ' '.join(comments) if comments else f"Query {query_index}"
                    section_title = comment_text

                    if query:
                        print(f"Executing: {section_title}")
                        self.cursor.execute(query)
                        rows = self.cursor.fetchall()
                        columns = [desc[0] for desc in self.cursor.description]
                        # Print result in console
                        print(tabulate(rows, headers=columns, tablefmt='grid'))

                        # write section title
                        writer.writerow([section_title])
                        # write header
                        writer.writerow(columns)
                        # write data rows
                        writer.writerows(rows)
                        # add empty rows as separator
                        writer.writerow([])
                        writer.writerow([])

                        query_index += 1

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


if __name__ == "__main__":
    args = parse_args()
    perf_report = PerformanceReport(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password
    )

    try:
        # run queries and create a report here
        perf_report.execute_query_from_file('performance_queries/queries.sql')
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'db_connection' in locals():
            perf_report.close()
