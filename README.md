## 1. Set up Python environment

1. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

## 2. Add datasets to the project

* Create a directory `dataset` and put `ad_events.csv`, `campaigns.csv` and `users.csv` files to the folder


## 3. Run docker compose file:

```bash
docker-compose up -d
```

What this file does:
* Starts a MySQL container named **set_mysql**.
* Creates a DB called **set_db**.
* Runs all .sql files in `./ddl_scripts` as initialization scripts in alphabetical order.
* Persists MySQL data in a volume so it's not lost when the container is stopped or deleted.
* Create a volume for all csv files we need to insert data to the DB

Stop and remove all containers, networks, and volumes defined in docker-compose.yml:

```bash
docker-compose down -v
```

## 4. Run python script to insert data into the DB:

```bash
# Using default connection parameters
python run.py

# Or specify custom connection parameters
python run.py --host localhost --database set_db --user set_user --password set_password
```

The script will:

* Create the `dataset_normalized` directory if it doesn't exist
* Process each dataset in sequence
* Save the normalized data to the output directory
* Transform all data in a way they match sql tables
* Save these files to the docker volume
* Insert data to the DB
* Remove unnecessary csv files

## 5. Run SQL queries from HW 3 and get a csv report
```bash
python py_scripts/performance_report.py
```

# Homework 3

## 1. To create schemas and run mongoDB container:

```bash
docker-compose up -d
```

What this file does:
* Starts a MySQL and MongoDB containers.
* Creates a MongoDB database called **set_db**.
* Runs all .js files in `./mongo_init` as initialization scripts in alphabetical order.
* Persists MongoDB data in a volume so it's not lost when the container is stopped or deleted.

## 2. Insert Data:

I used csv files to insert data into MongoDB. To do this you can
run this script:

```bash
python py_scripts/insert_data_to_mongo.py
```


## 3. Run performance queries and create a report:

```bash
python py_scripts/performance_report_mongo.py
```


