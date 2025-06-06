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

* Create a directory `dataset` and put `ad_events.csv`, `campaigns.csv` and `users.csv` files in it


## 3. Run docker compose file:

```bash
docker-compose up -d
```

What this file does:
* Starts a MySQL container named set_mysql.
* Creates a DB called **set_db**.
* Runs all .sql files in `./ddl_scripts` as initialization scripts in alphabetical order.
* Persists MySQL data in a volume so it's not lost when the container is stopped or deleted.

## 4. Run python script to insert data into the DB:

```bash
python run.py
```

The script will:

* Create the `dataset_normalized` directory if it doesn't exist
* Process each dataset in sequence
* Save the normalized data to the output directory
* Transform data before inserting them to the DB
* Insert data to the DB