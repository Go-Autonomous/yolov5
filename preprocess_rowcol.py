import split
from pathlib import Path
from preprocess_utils import find_missing_labels, copy_files_to_final_destination, table_transform

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

label2id = {
    "Table": 0,
    "Table head": None,
    "Table line": None,
    "Table column": None,
    "Table footer": None,
    "Table comments": None,
    "Table totals": 1,
    "Delivery address": 2,
    "Invoice address": 2,
    "Vendor address": 2,
    "Company address": 2,
}
label_pos = {label: id for id, label in enumerate(list(label2id.keys()))}


def main():
    # Create final destination for results if needed
    created_data_path = Path("datasets/created_data_rowcol")
    (created_data_path / "images").mkdir(exist_ok=True, parents=True)
    (created_data_path / "labels").mkdir(exist_ok=True, parents=True)

    copy_files_to_final_destination(src_path='preprocess-extra', dest_path='datasets/created_data_rowcol')
    find_missing_labels('datasets/created_data_rowcol/images', 'datasets/created_data_rowcol/labels')
    # split_data(labels_path='datasets/created_data_rowcol/labels',
    #            subset=['Table', 'Table head', 'Table line', 'Table column'],
    #            list_of_labels=label2id)
    table_transform(path='datasets/created_data_rowcol')
    find_missing_labels('datasets/created_data_rowcol/images', 'datasets/created_data_rowcol/labels')
    split.split_images_and_labels(path=Path("datasets/created_data_rowcol"))


if __name__ == "__main__":
    main()
