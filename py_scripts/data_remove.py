import shutil
from pathlib import Path


def remove_directory_contents(directory_path):
    """Remove all contents of a directory while keeping the directory itself"""
    try:
        # Convert to Path object for better path handling
        dir_path = Path(directory_path)

        if not dir_path.exists():
            print(f"Directory {directory_path} does not exist")
            return

        # Remove all contents
        for item in dir_path.iterdir():
            if item.is_file():
                item.unlink()  # delete the file
                print(f"Removed file: {item}")
            elif item.is_dir():
                shutil.rmtree(item)  # delete the directory and its contents
                print(f"Removed directory: {item}")

        print(f"Successfully cleaned directory: {directory_path}")

    except Exception as e:
        print(f"Error cleaning directory {directory_path}: {str(e)}")
        raise


def remove_data():
    directories_to_clean = ["dataset_normalized", "csv_data"]

    try:
        for directory in directories_to_clean:
            print(f"Starting cleanup of {directory}")
            remove_directory_contents(directory)

        print("Data cleanup completed successfully")

    except Exception as e:
        print(f"Error during data cleanup: {str(e)}")
        raise
