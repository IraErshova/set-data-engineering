from py_scripts.mysql.data_inserter import insert_data
from py_scripts.data_transormation.data_normalizer import normalize_datasets
from py_scripts.data_transormation.data_remove import remove_data
from py_scripts.data_transormation.data_transformer import transform_datasets
from py_scripts.mongo_db.insert_data_to_mongo import insert_data_to_mongo

if __name__ == "__main__":
    normalize_datasets()
    transform_datasets()
    insert_data()
    insert_data_to_mongo()
    remove_data()
