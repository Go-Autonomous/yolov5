import os
import shutil
from pdf2image import convert_from_path
from loguru import logger
from PIL import Image


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


def copy_files_to_final_destination(src_path, dest_path):

    delete_inside(os.path.join(dest_path, 'images'))
    delete_inside(os.path.join(dest_path, 'labels'))

    missing_counter = 0
    for filename in os.listdir(os.path.join(src_path, 'images')):
        image_path = os.path.join(src_path + '/images', filename)
        label_path = os.path.join(src_path + '/labels', filename.replace('.jpeg', '.txt'))
        try:
            shutil.copy2(image_path, os.path.join(dest_path, 'images'))
            shutil.copy2(label_path, os.path.join(dest_path, 'labels'))
        except:
            missing_counter += 1

    logger.debug(f"Number of unlabelled images: {missing_counter}")


def find_missing_labels(dir_images, dir_labels):
    """
    Method to find missing labels. In case some image miss labels, delete this image.
    """

    # loop over images and delete these for which we do not have labels
    for filename in os.listdir(dir_images):                                        # loop over files
        if filename.replace('.jpeg', '.txt') not in os.listdir(dir_labels):        # check existence
            os.remove(os.path.join(dir_images, filename))                          # delete

    # check sizes of both directories with images and labels, in case the size is not the same repeat the process
    # above and delete files with labels in case we do not have corresponding image
    if len(os.listdir(dir_images)) != len(os.listdir(dir_labels)):
        for filename in os.listdir(dir_labels):
            if filename.replace('.txt', '.jpeg') not in os.listdir(dir_images):
                os.remove(os.path.join(dir_labels, filename))


def rename_data(name, dir_images, dir_labels):
    """
    Method to rename new data in image and label folders based on current circumstances.

    name: str
        new file names
    """

    counter = 1
    for filename in os.listdir(dir_images):
        if counter < 10:
            os.rename(os.path.join(dir_images, filename),
                      os.path.join(dir_images, name + '_0' + str(counter) + '.jpeg'))
            os.rename(os.path.join(dir_labels, filename.replace('.jpeg', '.txt')),
                      os.path.join(dir_labels, name + '_0' + str(counter) + '.txt'))
        else:
            os.rename(os.path.join(dir_images, filename),
                      os.path.join(dir_images, name + '_' + str(counter) + '.jpeg'))
            os.rename(os.path.join(dir_labels, filename.replace('.jpeg', '.txt')),
                      os.path.join(dir_labels, name + '_' + str(counter) + '.txt'))

        counter += 1


def subset_labels(labels_path, subset, list_of_labels, merge_addresses=False):
    """
    Function to split labels just for needed objects for detection.

    folder: str
        path to folder with a new label files
    labels: list
        label's numbers for split
    """

    def manual_replace(s, char, index):
        return s[:index] + char + s[index + 1:]

    if merge_addresses:
        addresses_ids = [list_of_labels[part] for part in ["Invoice address", "Vendor address", "Company address"]]
    else:
        addresses_ids = []

    subset_ids = [list_of_labels[part] for part in subset] + addresses_ids

    transform = {str(label): number for label, number
                 in zip(subset_ids, list(range(len(subset))) + [len(subset)-1 for _ in range(len(addresses_ids))])
                 }

    # loop over files with labels
    for filename in os.listdir(labels_path):
        new_file = []
        file = open(os.path.join(labels_path, filename), 'r')
        # loop over lines with labels inside the file
        for line in file:
            for object_num, new_num in transform.items():
                # If wanted label
                if line[0] == object_num:
                    # Change the labels number starting from 0
                    line = manual_replace(line, str(new_num), 0)
                    # Save
                    new_file.append(line)
                    break
        file.close()
        os.remove(os.path.join(labels_path, filename))
        # in case we have found our objects, save into a new file in a new folder
        if len(new_file) > 0:
            with open(os.path.join(labels_path, filename), "w") as save_file:
                for row in new_file:
                    save_file.write(row)


def from_pdf_to_img(pdfs, imgs):
    """
    Function to convert pdfs into images.

    pdfs: str
        path to folder with PDFs
    imgs:
        path to save new created images
    """

    # loop over pdfs
    counter = 1
    size = len(os.listdir(pdfs))
    for pdf in os.listdir(pdfs):
        print('--- converting PDF ', counter, ' out of ', size, ' ---')
        counter += 1
        # convert into jpeg
        try:
            pages = convert_from_path(os.path.join(pdfs, pdf), 300)
            # save
            page_num = 1
            for page in pages:
                page.save(os.path.join(imgs, pdf.replace('.pdf', '') + str(page_num) + '.jpeg'), 'JPEG')
                page_num += 1
        except:
            print('Error: not PDF')


def join_head_line(path, final_path):
    # delete folder with a final destination
    delete_inside(folder=final_path)

    # *** For all annotations in a folder ***
    for file in os.listdir(path):
        name = file.split('.')[0]

        # Get table labels
        labels = open(os.path.join(path, name + ".txt"), "r").readlines()
        labels = [line.split() for line in labels]

        wanted_obj = list(filter(lambda x: int(x[0]) == 0 or int(x[0]) == 1, labels))
        # Save labels into .txt file
        with open(os.path.join(final_path, name + ".txt"), 'w') as f:
            first_obj = True
            for obj in wanted_obj:
                first_num = True
                for item in obj:
                    if first_num and first_obj:
                        f.write('0')
                        first_num = False
                        first_obj = False
                    elif first_num and not first_obj:
                        f.write("\n")
                        f.write('0')
                        first_num = False
                    else:
                        f.write(" " + str(item))


def table_transform(path: str):
    """
    Function to crop annotated PO for Vision 2.0 into just a table area and transform all labels related
    to inner table area into a corresponding format.
    :param path: str
        Path to folder with labelled images and corresponding .txt files with labels. Image and corresponding
        .txt files have to have the same name and be located in the same folder.
    :return: None
        Results are saved into folder "created_data" inside this repository.
    """
    path_images = os.path.join(path, 'images')
    path_labels = os.path.join(path, 'labels')

    # *** For all images in a folder ***
    for file in os.listdir(path_images):
        correct = True

        # *** Crop image based on annotation ***
        # Opens an image in RGB mode and delete the origin in the folder
        im = Image.open(os.path.join(path_images, file))
        os.remove(os.path.join(path_images, file))

        # Size of the image in pixels (size of original image)
        width, height = im.size

        # Get table labels and remove the original file
        labels = open(os.path.join(path_labels,  file.replace('.jpeg', '.txt')), "r").readlines()
        labels = [line.split() for line in labels]
        os.remove(os.path.join(path_labels, file.replace('.jpeg', '.txt')))

        # Get label objects
        table_obj = list(filter(lambda x: int(x[0]) == 0, labels))
        header_obj = list(filter(lambda x: int(x[0]) == 1, labels))
        line_obj = list(filter(lambda x: int(x[0]) == 2, labels))
        column_obj = list(filter(lambda x: int(x[0]) == 3, labels))

        # In case we have any table inside annotated document
        if table_obj:
            table = table_obj[0]
            # Setting the points for cropped image
            left = (float(table[1]) - float(table[3]) / 2) * width
            top = (float(table[2]) - float(table[4]) / 2) * height
            right = (float(table[1]) + float(table[3]) / 2) * width
            bottom = (float(table[2]) + float(table[4]) / 2) * height

            # Cropped image of above dimension
            # (It will not change original image)
            im1 = im.crop((left, top, right, bottom))

            # *** Transform old annotations inside the table ***
            # relative table coordinates transformation
            top_rel = top / height
            bottom_rel = bottom / height
            left_rel = left / width
            right_rel = right / width

            # object transformation
            obj_container = [header_obj, line_obj, column_obj]
            transformed_container = []
            for ind, obj_type in enumerate(obj_container):
                for instance in obj_type:
                    tmp_line = [
                        ind,
                        (float(instance[1]) - left_rel) / (right_rel - left_rel),
                        (float(instance[2]) - top_rel) / (bottom_rel - top_rel),
                        float(instance[3]) / (right_rel - left_rel),
                        float(instance[4]) / (bottom_rel - top_rel),
                    ]

                    # check for overlapping
                    bottom_overlap = float(instance[2]) + float(instance[4]) / 2 - bottom_rel
                    top_overlap = top_rel - (float(instance[2]) - float(instance[4]) / 2)
                    left_overlap = left_rel - (float(instance[1]) - float(instance[3]) / 2)
                    right_overlap = float(instance[1]) + float(instance[3]) / 2 - right_rel
                    if bottom_overlap > 0:
                        tmp_line[2] = tmp_line[2] - (bottom_overlap / (bottom_rel - top_rel)) / 2
                        tmp_line[4] = tmp_line[4] - bottom_overlap / (bottom_rel - top_rel)
                    if top_overlap > 0:
                        tmp_line[2] = tmp_line[2] + (top_overlap / (bottom_rel - top_rel)) / 2
                        tmp_line[4] = tmp_line[4] - top_overlap / (bottom_rel - top_rel)
                    if right_overlap > 0:
                        tmp_line[1] = tmp_line[1] - (right_overlap / (right_rel - left_rel)) / 2
                        tmp_line[3] = tmp_line[3] - right_overlap / (right_rel - left_rel)
                    if left_overlap > 0:
                        tmp_line[1] = tmp_line[1] + (left_overlap / (right_rel - left_rel)) / 2
                        tmp_line[3] = tmp_line[3] - left_overlap / (right_rel - left_rel)

                    # never go above 1.0
                    tmp_line[3] = min(tmp_line[3], 1.0)
                    tmp_line[4] = min(tmp_line[4], 1.0)

                    # Check if bad annotation
                    if any(i < 0 or i > 1 for i in tmp_line[1:]):
                        correct = False

                    transformed_container.append(tmp_line)

            if correct:
                # Save the image
                im1.save(os.path.join(path_images, file))
                # Save labels into .txt file
                with open(os.path.join(path_labels, file.replace('.jpeg', '.txt')), "w") as f:
                    first_obj = True
                    for obj in transformed_container:
                        first_num = True
                        for item in obj:
                            if first_num and first_obj:
                                f.write(str(item))
                                first_num = False
                                first_obj = False
                            elif first_num and not first_obj:
                                f.write("\n")
                                f.write(str(item))
                                first_num = False
                            else:
                                f.write(" " + str(item))
