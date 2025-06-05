from py_scripts.data_inserter import transform_and_insert_data
from py_scripts.data_normalizer import normalize_datasets

if __name__ == "__main__":
    normalize_datasets()
    transform_and_insert_data()