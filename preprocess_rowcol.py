import split
from pathlib import Path
from preprocess_utils import find_missing_labels, copy_files_to_final_destination, table2rowcolhead

label_lst = [
    "Table",
    "Table head",
    "Table line",
    "Table column",
    "Table footer",
    "Table comments",
    "Table totals",
    "Delivery address",
    "Invoice address",
    "Vendor address",
    "Company address",
]


def main():
    # Create final destination for results if needed
    created_data_path = Path("datasets/created_data_rowcol")
    (created_data_path / "images").mkdir(exist_ok=True, parents=True)
    (created_data_path / "labels").mkdir(exist_ok=True, parents=True)

    copy_files_to_final_destination(src_path='preprocess', dest_path='datasets/created_data_rowcol')
    find_missing_labels('datasets/created_data_rowcol/images', 'datasets/created_data_rowcol/labels')
    table2rowcolhead(path='datasets/created_data_rowcol')
    find_missing_labels('datasets/created_data_rowcol/images', 'datasets/created_data_rowcol/labels')
    split.split_images_and_labels(path=Path("datasets/created_data_rowcol"))


if __name__ == "__main__":
    main()
