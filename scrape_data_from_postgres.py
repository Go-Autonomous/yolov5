import httpx
import json
from google.cloud import storage
from urllib.parse import urlparse
from loguru import logger
from settings import settings
import os, shutil

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
    with open('preprocess/labels/' + annotation_name, 'w') as f:
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


def delete_content_of_folder(path_to_folder):
    for filename in os.listdir(path_to_folder):
        try:
            file_path = os.path.join(path_to_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_postgres_data_urls(access_token='local'):
    # Initialization of output
    data_urls = []
    # Right now only for production
    if settings.ENVIRONMENT == 'production':
        with httpx.Client() as client:
            if access_token == 'local':
                access_token_credentials = settings.SAGA_TOKEN
            else:
                access_token_credentials = access_token.credentials

            # *** GET DATA FROM DATABASE ***
            url = f"{settings.POSTGREST_URL}/content_annotation"
            headers = {"Authorization": f"Bearer {access_token_credentials}", "Accept-Profile": "bc"}
            response = client.get(url, headers=headers)

            if not 200 <= response.status_code < 300:
                logger.info(f"Data not downloaded with an error: {response}")
            else:
                data_urls = [ps["annotation_url"] for ps in response.json() if ps['annotation_type'] == 'vision']
    return data_urls


def decode_gcs_url(url):
    p = urlparse(url)
    path = p.path[1:].split('/', 1)
    bucket, file_path = path[0], path[1]
    return bucket, file_path


def download_blob(url):
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
    # TODO pick only validated data
    for num, url in enumerate(data_paths):
        if (num + 1) % 100 == 0:
            print(f'--- Already downloaded {num + 1} files out of {len(data_paths)} ---')
        json_file = download_blob(url)
        if json_file:
            task_id = json_file['task']['id']
            # Remove annotations which were skipped over the time
            if task_id in annotations.keys() and not json_file['task']['is_labeled']:
                del annotations[task_id]
            # and add only the ones which were annotated
            elif json_file['task']['is_labeled'] and not json_file['was_cancelled']:
                if needs_to_be_validated:
                    try:
                        validation_result_obj = [obj for obj in json_file['result'] if obj['from_name'] == 'Validation']
                        if validation_result_obj:
                            validation_result = validation_result_obj[0]['value']['choices']
                            if 'Validated' in validation_result:
                                annotations[task_id] = json_file
                    except Exception as e:
                        logger.debug(f'Task was not annotated with an error: {e}')
                else:
                    annotations[task_id] = json_file

    return annotations


def download_legacy_data():
    # Instantiates a client
    storage_client = storage.Client()

    # Get GCS bucket
    bucket = storage_client.get_bucket('ga_vision_images')

    # Get blobs in specific subdirectory
    blobs_specific = list(bucket.list_blobs(prefix='legacy/'))
    for num, blob in enumerate(blobs_specific):
        try:
            if (num + 1) % 100 == 0:
                print(f'--- Already downloaded {num + 1} images out of {len(blobs_specific)} ---')
            blob.download_to_filename('preprocess/images/' + '/'.join(blob.name.split('/')[2:]))
        except Exception as e:
            print(f'--- Failed to download {blob.name} with {e} ---')

    # Get GCS bucket
    bucket = storage_client.get_bucket('ga_vision_annotations')

    # Get blobs in specific subdirectory
    blobs_specific = list(bucket.list_blobs(prefix='legacy/'))
    for num, blob in enumerate(blobs_specific):
        try:
            if (num + 1) % 100 == 0:
                print(f'--- Already downloaded {num + 1} labels out of {len(blobs_specific)} ---')
            blob.download_to_filename('preprocess/labels/' + '/'.join(blob.name.split('/')[2:]))
        except Exception as e:
            print(f'--- Failed to download {blob.name} with {e} ---')


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
            blob.download_to_filename('preprocess/images/' + image_name)
        except Exception as e:
            print(f'--- Failed to download {image_name} with {e} ---')


def get_training_data(access_token='local', needs_to_be_validated=False):
    delete_content_of_folder('preprocess/images')
    delete_content_of_folder('preprocess/labels')

    # get legacy data
    download_legacy_data()

    # get label studio data
    urls = get_postgres_data_urls(access_token)
    annotated_data_in_jsons = download_annotated_data_from_bucket(urls, needs_to_be_validated)
    download_label_studio_data(annotated_data_in_jsons)


if __name__ == '__main__':
    get_training_data(needs_to_be_validated=True)
