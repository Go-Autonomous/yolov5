import split
from preprocess_utils import copy_files_to_final_destination, find_missing_labels, tables2cols
from pathlib import Path

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
    created_data_path = Path("datasets/created_data_rowcol_base")
    (created_data_path / "images").mkdir(exist_ok=True, parents=True)
    (created_data_path / "labels").mkdir(exist_ok=True, parents=True)

    copy_files_to_final_destination(src_path="preprocess", dest_path="datasets/created_data_rowcol_base")
    find_missing_labels("datasets/created_data_rowcol_base/images", "datasets/created_data_rowcol_base/labels")
    tables2cols(path="datasets/created_data_rowcol_base")
    find_missing_labels("datasets/created_data_rowcol_base/images", "datasets/created_data_rowcol_base/labels")
    split.split_images_and_labels(path=Path("datasets/created_data_rowcol_base"))


if __name__ == "__main__":
    main()
