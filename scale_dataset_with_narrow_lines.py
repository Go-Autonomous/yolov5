import os
import numpy as np
import shutil

def delete_inside(folder: str):
    """
    Function to delete all files inside folder.
    :param folder: str
        Path to folder
    :return: None
    """
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def main():
    counter = 0
    labels_folder = 'datasets/created_data_rowcol/labels/train_split'
    images_folder = 'datasets/created_data_rowcol/images/train_split'
    labels_save = 'datasets_scale/labels'
    images_save = 'datasets_scale/images'

    delete_inside(labels_save)
    delete_inside(images_save)

    for filename in os.listdir(labels_folder):
        with open(os.path.join(labels_folder, filename), 'r') as f:
            lines = f.readlines()

        heights_of_lines = [float(line.split(' ')[4]) for line in lines if line[0] == '1']
        high_levels = [0.1, 0.07, 0.05, 0.03, 0.02, 0.01]
        # high_levels = [0.05]
        line_counts = [2, 3, 4, 5, 6, 7, 8]
        # line_counts = [5]
        for level in high_levels:
            if len(heights_of_lines) > 1 and np.mean(heights_of_lines) < level:
                counter += 1
                print('first', counter)
                # copy labels
                shutil.copy(os.path.join(labels_folder, filename),
                            os.path.join(labels_save, filename.replace('.txt', f'_{counter}.txt')))
                # copy images
                try:
                    shutil.copy(os.path.join(images_folder, filename.replace('.txt', '.jpeg')),
                                os.path.join(images_save, filename.replace('.txt', f'_{counter}.jpeg')))
                except:
                    shutil.copy(os.path.join(images_folder, filename.replace('.txt', '.png')),
                                os.path.join(images_save, filename.replace('.txt', f'_{counter}.png')))


        for count in line_counts:
            if len(heights_of_lines) > count and np.mean(heights_of_lines) < 0.1:
                counter += 1
                print('second', counter)
                # copy labels
                shutil.copy(os.path.join(labels_folder, filename),
                            os.path.join(labels_save, filename.replace('.txt', f'_{counter}.txt')))
                # copy images
                try:
                    shutil.copy(os.path.join(images_folder, filename.replace('.txt', '.jpeg')),
                                os.path.join(images_save, filename.replace('.txt', f'_{counter}.jpeg')))
                except:
                    shutil.copy(os.path.join(images_folder, filename.replace('.txt', '.png')),
                                os.path.join(images_save, filename.replace('.txt', f'_{counter}.png')))


if __name__ == '__main__':
    main()

    labels_save = 'datasets_scale/labels'
    images_save = 'datasets_scale/images'

    dataset_folder_labels = 'datasets/created_data_rowcol/labels/train_split'
    dataset_folder_images = 'datasets/created_data_rowcol/images/train_split'

    for filename in os.listdir(labels_save):
        shutil.copy(os.path.join(labels_save, filename), os.path.join(dataset_folder_labels, filename))
    for filename in os.listdir(images_save):
        shutil.copy(os.path.join(images_save, filename), os.path.join(dataset_folder_images, filename))