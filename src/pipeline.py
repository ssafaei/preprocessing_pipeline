import argparse
import os
import sys
import shutil
import SimpleITK as sitk
from shutil import move
from registration.registration import Registration
import dicom2nifti
# disable the slice increment consistency check
import dicom2nifti.settings as settings
settings.disable_validate_slice_increment()

def convert_dicom_to_nifti(dicom_folder, nii_filename, save_dir):
    tmp_folder = os.path.join(save_dir, "tmp_folder")
    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)
    dicom2nifti.convert_directory(dicom_folder, tmp_folder, compression=True, reorient=True)
    # renames the file
    for fname in os.listdir(tmp_folder):
        if fname.endswith('.nii.gz'):
            move(os.path.join(tmp_folder, fname), os.path.join(save_dir, nii_filename))
            os.removedirs(tmp_folder)

def reorient(image):
    reorientation = sitk.DICOMOrientImageFilter()
    reorientation.SetDesiredCoordinateOrientation("RAS")
    ras_img = orient.Execute(image)
    return ras_img


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="A brain MRI image registration pipeline which takes 4 structural "
                                                 "brain MRIs (T1, T1CE, T2, FLAIR) as input")

    parser.add_argument("-t1", "--t1", type=os.path.abspath, help="path to t1 nifti image/ dicom folder")
    parser.add_argument("-t2", "--t2", type=os.path.abspath, help="path to t2 nifti image/ dicom folder")
    parser.add_argument("-fl", "--flair", type=os.path.abspath, help="path to flair nifti image/ dicom folder")
    parser.add_argument("-t1ce", "--t1ce", type=os.path.abspath, help="path to t1ce nifti image/ dicom folder")
    parser.add_argument("-o", "--output", type=os.path.abspath, help="path to the output folder", required=True)

    args = parser.parse_args()

    t1 = args.t1
    t2 = args.t2
    flair = args.flair
    t1ce = args.t1ce
    sri24 = os.path.join(os.path.dirname(os.path.abspath(__file__)),"../resources/sri24/spgr_unstrip.nii")
    save_dir = args.output

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    shutil.copyfile(sri24, os.path.join(save_dir, "sri24.nii"))

    # dicom to nifti
    if t1 and os.path.isdir(t1):
        nii_filename = "t1.nii.gz"
        convert_dicom_to_nifti(t1, nii_filename, save_dir)
        t1 = os.path.join(save_dir, nii_filename)
    if t2 and os.path.isdir(t2):
        nii_filename = "t2.nii.gz"
        convert_dicom_to_nifti(t2, nii_filename, save_dir)
        t2 = os.path.join(save_dir, nii_filename)
    if flair and os.path.isdir(flair):
        nii_filename = "flair.nii.gz"
        convert_dicom_to_nifti(flair, nii_filename, save_dir)
        flair = os.path.join(save_dir, nii_filename)
    if t1ce and os.path.isdir(t1ce):
        nii_filename = "t1ce.nii.gz"
        convert_dicom_to_nifti(t1ce, nii_filename, save_dir)
        t1ce = os.path.join(save_dir, nii_filename)

    # t1ce to SRI-24
    if t1ce and os.path.isfile(t1ce):
        reg = Registration()
        reg.set_images(fixed=sri24, moving=t1ce)
        save_path = os.path.join(save_dir, "t1ce_to_sri24.nii.gz")
        reg.execute(save_path)

    # t1 to t1ce
    if t1 and os.path.isfile(t1):
        reg = Registration()
        t1ce_reg = "../output/t1ce_to_sri24.nii.gz"
        reg.set_images(fixed=t1ce_reg, moving=t1)
        save_path = os.path.join(save_dir, "t1_to_t1ce.nii.gz")
        reg.execute(save_path)

    # t2 to t1ce
    if t2 and os.path.isfile(t2):
        reg = Registration()
        t1ce_reg = "../output/t1ce_to_sri24.nii.gz"
        reg.set_images(fixed=t1ce_reg, moving=t2)
        save_path = os.path.join(save_dir, "t2_to_t1ce.nii.gz")
        reg.execute(save_path)

    # flair to t1ce
    if flair and os.path.isfile(flair):
        reg = Registration()
        t1ce_reg = "../output/t1ce_to_sri24.nii.gz"
        reg.set_images(fixed=t1ce_reg, moving=flair)
        save_path = os.path.join(save_dir, "flair_to_t1ce.nii.gz")
        reg.execute(save_path)

