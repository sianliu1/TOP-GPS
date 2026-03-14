import json
import os
import shutil


def write_json_file():
    path = 'dataset.json'

    with open(path, 'r') as file:
        data = json.load(file)

    data['labels'] = {"0": "background",
                      "1": "nodule"}


    data_path = r'E:\郭志飞\nodlue_data'

    train_list = os.listdir(os.path.join(data_path, 'imagesTr'))
    test_list = os.listdir(os.path.join(data_path, 'imagesTs'))

    data['numTraining'] = len(train_list)
    data['numTest'] = len(test_list)
    training_data = []
    testing_data = []

    for i in train_list:
        tmp = {}
        tmp['image'] = f'./imagesTr/'+i
        tmp['label'] = f'./labelsTr/'+i
        training_data.append(tmp)

    for i in test_list:
        tmp = {}
        tmp['image'] = f'./imagesTs/'+i
        tmp['label'] = f'./labelsTs/'+i
        testing_data.append(tmp)

    data['training'] = training_data
    data['test'] = testing_data

    vaild_data = [{'image':'./imagesTr/'+train_list[15],
                   'label':'./labelsTr/'+train_list[15]}]

    data['validation'] = vaild_data

    out_path = data_path + '/dataset.json'
    with open(out_path, 'w') as file:
        json.dump(data, file)

def make_train_data():
    path =  r'F:\数据\lung\金标准\210套胸肺金标准数据汇总'
    out_path = r'E:\郭志飞\vessel'

    fold_list = os.listdir(path)

    image_name1 = 'imagesTr'
    label_name1 = 'labelsTr'
    image_name2 = 'imagesTs'
    label_name2 = 'labelsTs'

    image_path1 = os.path.join(path, image_name1)
    label_path1 = os.path.join(path, label_name1)
    image_path2 = os.path.join(path, image_name2)
    label_path2 = os.path.join(path, label_name2)

    out_image_path1 = os.path.join(out_path, image_name1)
    out_label_path1 = os.path.join(out_path, label_name1)
    out_image_path2 = os.path.join(out_path, image_name2)
    out_label_path2 = os.path.join(out_path, label_name2)

    if not os.path.exists(out_image_path1):
        os.makedirs(out_image_path1)
        os.makedirs(out_label_path1)
        os.makedirs(out_image_path2)
        os.makedirs(out_label_path2)

    idx = 0
    for i in os.listdir(image_path1):
        src1 = os.path.join(image_path1, i)
        dst1 = os.path.join(out_image_path1, f'vessel_{idx:03}.nii.gz')

        tmp_label_name =  i[0:i.rfind('_')]+'.nii.gz'

        src2 = os.path.join(label_path1, tmp_label_name)

        dst2 = os.path.join(out_label_path1, f'vessel_{idx:03}.nii.gz')

        shutil.copy(src1, dst1)
        shutil.copy(src2, dst2)
        idx = idx + 1


def cp_nodule_data():
    path = r'F:\数据\lung\金标准\肺结节金标准数据\label_nodule'
    img_path = r'F:\数据\lung\金标准\肺结节金标准数据\image'

    out_path = r'E:\郭志飞\nodlue_data'
    image_name = 'imagesTr'
    label_name = 'labelsTr'


    os.makedirs(os.path.join(out_path, image_name))
    os.makedirs(os.path.join(out_path, label_name))

    img_list = os.listdir(img_path)
    idx = 0

    for i in os.listdir(path):

        if i not in img_list:
            continue

        src1 = os.path.join(path, i)
        dst1 = os.path.join(out_path, label_name, f'nodule_{idx:03}.nii.gz')

        src2 = os.path.join(img_path, i)
        dst2 = os.path.join(out_path, image_name, f'nodule_{idx:03}.nii.gz')

        shutil.copy(src1, dst1)
        shutil.copy(src2, dst2)
        idx = idx + 1





if __name__ == '__main__':
    write_json_file()