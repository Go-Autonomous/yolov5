import split
from preprocess_utils import copy_files_to_final_destination, find_missing_labels, subset_labels
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
label2id = {label: id for id, label in enumerate(label_lst)}


def main():
    # Create final destination for results if needed
    created_data_path = Path("datasets/created_data_table")
    (created_data_path / "images").mkdir(exist_ok=True, parents=True)
    (created_data_path / "labels").mkdir(exist_ok=True, parents=True)

    copy_files_to_final_destination(src_path="preprocess", dest_path="datasets/created_data_table")
    subset_labels(
        labels_path="datasets/created_data_table/labels",
        subset=["Table", "Table totals", "Delivery address"],
        list_of_labels=label2id,
        merge_addresses=True,
    )
    find_missing_labels("datasets/created_data_table/images", "datasets/created_data_table/labels")
    split.split_images_and_labels(path=Path("datasets/created_data_table"))


if __name__ == "__main__":
    main()
