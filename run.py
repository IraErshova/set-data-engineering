from py_scripts.data_inserter import insert_data
from py_scripts.data_normalizer import normalize_datasets
from py_scripts.data_remove import remove_data
from py_scripts.data_transformer import transform_datasets
from py_scripts.insert_data_to_mongo import insert_data_to_mongo

if __name__ == "__main__":
    normalize_datasets()
    transform_datasets()
    insert_data()
    insert_data_to_mongo()
    remove_data()
