import os
import shutil
import numpy as np
from pathlib import Path
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
        label_path = os.path.join(src_path + '/labels', filename.replace('.png', '.txt'))
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
        if filename.replace('.png', '.txt') not in os.listdir(dir_labels):        # check existence
            os.remove(os.path.join(dir_images, filename))                          # delete

    # check sizes of both directories with images and labels, in case the size is not the same repeat the process
    # above and delete files with labels in case we do not have corresponding image
    if len(os.listdir(dir_images)) != len(os.listdir(dir_labels)):
        for filename in os.listdir(dir_labels):
            if filename.replace('.txt', '.png') not in os.listdir(dir_images):
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
                      os.path.join(dir_images, name + '_0' + str(counter) + '.png'))
            os.rename(os.path.join(dir_labels, filename.replace('.png', '.txt')),
                      os.path.join(dir_labels, name + '_0' + str(counter) + '.txt'))
        else:
            os.rename(os.path.join(dir_images, filename),
                      os.path.join(dir_images, name + '_' + str(counter) + '.png'))
            os.rename(os.path.join(dir_labels, filename.replace('.png', '.txt')),
                      os.path.join(dir_labels, name + '_' + str(counter) + '.txt'))

        counter += 1


def subset_labels(labels_path, label_id, label_num):
    """
    Function to split labels just for needed objects for detection.

    folder: str
        path to folder with a new label files
    labels: list
        label's numbers for split
    """

    def manual_replace(s, char, index):
        return s[:index] + char + s[index + 1:]

    transform = {str(label_num[item]): label_id[item] for item in label_id.keys() if label_id[item] is not None}

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
        # convert into png
        try:
            pages = convert_from_path(os.path.join(pdfs, pdf), 300)
            # save
            page_num = 1
            for page in pages:
                page.save(os.path.join(imgs, pdf.replace('.pdf', '') + str(page_num) + '.png'), 'png')
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


def table2rowcolhead(path: str):
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
        labels = open(os.path.join(path_labels,  file.replace('.png', '.txt')), "r").readlines()
        labels = [line.split() for line in labels]
        os.remove(os.path.join(path_labels, file.replace('.png', '.txt')))

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
                with open(os.path.join(path_labels, file.replace('.png', '.txt')), "w") as f:
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


def tables2cols(path):

    path_images = os.path.join(path, 'images')
    path_labels = os.path.join(path, 'labels')

    for file in os.listdir(path_images):
        image = Image.open(os.path.join(path_images, file))
        width, height = image.size
        os.remove(os.path.join(path_images, file))

        # Get table labels and delete the original file
        labels = open(os.path.join(path_labels, file.replace('.png', '.txt')), "r").readlines()
        labels = [line.split() for line in labels]
        os.remove(os.path.join(path_labels, file.replace('.png', '.txt')))

        # Get label objects
        header_objs = list(filter(lambda x: int(x[0]) == 1, labels))
        line_objs = list(filter(lambda x: int(x[0]) == 2, labels))
        column_objs = list(filter(lambda x: int(x[0]) == 3, labels))

        for i, column_obj in enumerate(column_objs):
            # Setting the points for cropped image
            column_x_center = float(column_obj[1])
            column_y_center = float(column_obj[2])
            column_width = float(column_obj[3])
            column_height = float(column_obj[4])

            if column_height < 0.01 or column_width < 0.01:
                continue

            left = (column_x_center - column_width / 2) * width
            top = (column_y_center - column_height / 2) * height
            right = (column_x_center + column_width / 2) * width
            bottom = (column_y_center + column_height / 2) * height

            col_image = image.crop((left, top, right, bottom))
            col_width, col_height = col_image.size

            # *** Transform old annotations inside the column ***
            # relative column coordinates transformation
            top_rel = top / height
            bottom_rel = bottom / height
            left_rel = left / width
            right_rel = right / width

            other_objs = header_objs + line_objs

            transformed_inside_col_row = []
            for other_obj in other_objs:
                # Setting the points for cropped image (relative)
                obj_type = int(other_obj[0]) - 1
                other_obj_x_center = (float(other_obj[1]) - left_rel) / (right_rel - left_rel)
                other_obj_y_center = (float(other_obj[2]) - top_rel) / (bottom_rel - top_rel)
                other_obj_width = (float(other_obj[3])) / (right_rel - left_rel)
                other_obj_height = (float(other_obj[4])) / (bottom_rel - top_rel)

                if other_obj_width > 1:
                    inside_col_x_center = 0.5
                    inside_col_width = 1
                else:
                    inside_col_x_center = other_obj_x_center
                    inside_col_width = other_obj_width

                if other_obj_height > 1:
                    inside_col_y_center = 0.5
                    inside_col_height = 1
                else:
                    inside_col_y_center = other_obj_y_center
                    inside_col_height = other_obj_height

                if other_obj_height < 0.01 or other_obj_width < 0.01:
                    continue

                # resize to fit new cropped image
                tmp_obj = [obj_type, inside_col_x_center, inside_col_y_center, inside_col_width, inside_col_height]

                # Test if the inside is just blank!
                obj_left = (inside_col_x_center - inside_col_width / 2) * col_width
                obj_top = (inside_col_y_center - inside_col_height / 2) * col_height
                obj_right = (inside_col_x_center + inside_col_width / 2) * col_width
                obj_bottom = (inside_col_y_center + inside_col_height / 2) * col_height

                gs_col_obj_image = col_image.crop((obj_left, obj_top, obj_right, obj_bottom)).convert("1")
                gs_col_obj_image = np.array(gs_col_obj_image)
                frac_white = gs_col_obj_image.sum() / (gs_col_obj_image.shape[0] * gs_col_obj_image.shape[1])
                tmp_obj = [str(obj) for obj in tmp_obj]
                txt_row = " ".join(tmp_obj)
                if frac_white < 0.99:
                    transformed_inside_col_row.append(txt_row)

            col_image.save(path_images / Path(f"{file.replace('.png', '')}_{i}" + '.png'))
            # Save labels into .txt file
            with open(path_labels / Path(f"{file.replace('.png', '')}_{i}" + '.txt'), "w") as f:
                f.writelines(["%s\n" % item for item in transformed_inside_col_row])
