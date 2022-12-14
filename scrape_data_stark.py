import httpx
import json
import os
import shutil
from google.cloud import storage
from urllib.parse import urlparse
from loguru import logger


label_dictionary = {
    "Table": 0,
    "Table head": 1,
    "Table line": 2,
    "Table column": 3,
    "Table footer": 4,
    "Comments": 5,
    "Table totals": 6,
    "Delivery address": 7,
    "Vendor address": 8,
    "Company address": 9,
    "Invoice address": 10,
    "In footer comments": 11,
    "Between line comments": 12,
    "In line comments": 13,
    "End of table comments": 14,
    "Above table comments": 15,
    "Below table footer comments": 16,
}


def json_to_yolo(input_json, annotation_name):
    with open('preprocess_stark/labels/' + annotation_name, 'w') as f:
        for annotation in input_json['result']:
            try:
                x_top = annotation['value']['x']
                y_top = annotation['value']['y']
                width = annotation['value']['width']
                height = annotation['value']['height']
                label = annotation['value']['rectanglelabels'][0]

                yolo_x_middle = (x_top + width/2)/100
                yolo_y_middle = (y_top + height/2)/100
                yolo_width = width/100
                yolo_height = height/100
                yolo_label_num = label_dictionary[label]

                final_string = f"{yolo_label_num} {yolo_x_middle} {yolo_y_middle} {yolo_width} {yolo_height}"

                f.write(final_string)
                f.write('\n')

            except Exception as e:
                pass


def delete_content_of_folder(path_to_folder: str) -> None:
    for filename in os.listdir(path_to_folder):
        try:
            file_path = os.path.join(path_to_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def decode_gcs_url(url: str):
    p = urlparse(url)
    path = p.path[1:].split('/', 1)
    bucket, file_path = path[0], path[1]
    return bucket, file_path


def download_blob(url: str) -> dict:
    annotation = {}
    if url:
        storage_client = storage.Client()
        bucket, file_path = decode_gcs_url(url)
        bucket = storage_client.bucket(bucket)
        blob = bucket.blob(file_path)
        annotation = json.loads(blob.download_as_text())

    return annotation


def download_annotated_data_from_bucket(data_paths, needs_to_be_validated):
    annotations = {}
    for num, url in enumerate(data_paths):
        if (num + 1) % 100 == 0:
            print(f'--- Already downloaded {num + 1} files out of {len(data_paths)} ---')
        json_file = download_blob(url)
        if json_file:
            try:
                task_id = json_file['task']['id']
                nature_of_annotation = [obj['value']['choices'][0] for obj in json_file['result']
                                        if obj['from_name'] == 'Validation']

                # Remove annotations which were skipped over the time
                if task_id in annotations.keys() and not json_file['task']['is_labeled']:
                    del annotations[task_id]
                # and add only the ones which were annotated and wasn't deleted
                elif (json_file['task']['is_labeled'] and not json_file['was_cancelled']
                      and 'Deleted' not in nature_of_annotation):
                    if needs_to_be_validated:
                        if 'Validated' in nature_of_annotation:
                            annotations[task_id] = json_file
                    else:
                        annotations[task_id] = json_file
            except Exception as e:
                logger.info(f'Annotation was not downloaded from gcp with an error: {e}')

    return annotations


def download_label_studio_data(annotated_data_in_jsons):
    # Instantiates a client
    storage_client = storage.Client()

    # Get GCS bucket
    bucket = storage_client.get_bucket('ga_vision_images')

    for num, json_annotation in enumerate(annotated_data_in_jsons.values()):
        if (num + 1) % 100 == 0:
            print(f'--- Already processed {num + 1} annotations out of {len(annotated_data_in_jsons.values())} ---')
        image_path = json_annotation['task']['data']['image'].replace('gs://ga_vision_images/', '')
        image_name = '/'.join(image_path.split('/')[1:])
        annotation_name = ''.join(image_name.split('.')[:-1]) + '.txt'

        json_to_yolo(json_annotation, annotation_name)

        try:
            blob = bucket.blob(image_path)
            blob.download_to_filename('preprocess_stark/images/' + image_name)
        except Exception as e:
            print(f'--- Failed to download {image_name} with {e} ---')


def get_bucket_data_urls(specific_org: str = ''):
    storage_client = storage.Client()

    folder_in_bucket = storage_client.list_blobs('ga_vision_annotations', prefix=specific_org)
    return [blob.public_url for blob in folder_in_bucket if blob.name != 'Stark/']


def get_training_data(needs_to_be_validated: bool = False, specific_org: str = '') -> None:
    delete_content_of_folder('preprocess_stark/images')
    delete_content_of_folder('preprocess_stark/labels')

    # get label studio data
    urls = get_bucket_data_urls(specific_org)
    annotated_data_in_jsons = download_annotated_data_from_bucket(urls, needs_to_be_validated)
    download_label_studio_data(annotated_data_in_jsons)


if __name__ == '__main__':
    get_training_data(needs_to_be_validated=True, specific_org='Stark')
