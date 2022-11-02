import split
from preprocess_utils import copy_files_to_final_destination, find_missing_labels, subset_labels
from pathlib import Path


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
    created_data_path = Path("datasets_stark/created_data_table")
    (created_data_path / "images").mkdir(exist_ok=True, parents=True)
    (created_data_path / "labels").mkdir(exist_ok=True, parents=True)

    copy_files_to_final_destination(src_path="preprocess_stark", dest_path="datasets_stark/created_data_table")
    copy_files_to_final_destination(src_path="preprocess", dest_path="datasets_stark/created_data_table", delete_content=False)
    subset_labels(
        labels_path="datasets_stark/created_data_table/labels",
        label_id=label2id,
        label_num=label_pos,
    )
    find_missing_labels("datasets_stark/created_data_table/images", "datasets_stark/created_data_table/labels")
    split.split_images_and_labels(path=Path("datasets_stark/created_data_table"))


if __name__ == "__main__":
    main()
