import os
from pathlib import Path
import nibabel
import nibabel.processing
import SimpleITK as sitk
import numpy as np
from skimage.transform import resize
import matplotlib.pyplot as plt


def normalise(image):
    """
    z-score normalisation
    """
    z = np.std(image)
    mean = np.mean(image)
    image = (image - mean) / z
    return image


def correct_by_n4(image):
    """
    N4 Bias correction
    """
    corrector = sitk.N4BiasFieldCorrectionImageFilter()
    number_fitting_levels = 4

    corrector.SetMaximumNumberOfIterations([int(1)] * number_fitting_levels)
    corrected_image = corrector.Execute(image)

    return corrected_image


class Registration(object):

    def __init__(self):
        self._fixed_path = None
        self._moving_path = None
        self._registered_image = None
        self._voxel_sizes = (1.0, 1.0, 1.0)
        self._voxel_unit = "mm"
        self._fixed_meta = None
        self._moving_meta = None
        self._fixed_meta = None
        self._moving_meta = None

    def set_images(self, fixed, moving):
        self._fixed_path = Path(fixed)
        self._moving_path = Path(moving)

    def load_Nifti(self, path):
        """
        Loads a volumetric Nifti file. It returns a volume with the file's data and its metadata.
        """
        meta = nibabel.load(path)
        data = meta.get_fdata()

        while data.ndim > 3:
            data = np.squeeze(data, axis=-1)

        return data, meta

    def execute(self, save_path=None):
        # shape = (H, W, D)
        fixed_arr, fixed_meta = self.load_Nifti(self._fixed_path)
        moving_arr, moving_meta = self.load_Nifti(self._moving_path)
        self._fixed_meta = fixed_meta
        self._moving_meta = moving_meta

        moving_arr = self._resize(fixed_arr, moving_arr)

        fixed_arr_normalised = normalise(fixed_arr)
        moving_arr_normalised = normalise(moving_arr)

        # fixed_idx = int(fixed_arr.shape[2] / 2)
        # moving_idx = int(moving_arr.shape[2] / 2)
        # fixed_itk = sitk.GetImageFromArray(fixed_arr_normalised[:, :, fixed_idx])
        # moving_itk = sitk.GetImageFromArray(moving_arr_normalised[:, :, moving_idx])

        fixed_itk = sitk.GetImageFromArray(fixed_arr_normalised)
        moving_itk = sitk.GetImageFromArray(moving_arr_normalised)

        # fixed_itk = correct_by_n4(fixed_arr)
        # moving_itk = correct_by_n4(moving_arr)

        initial_transform = sitk.CenteredTransformInitializer(fixed_itk, moving_itk,
                                                              sitk.Euler3DTransform(),
                                                              sitk.CenteredTransformInitializerFilter.GEOMETRY)
        registration_method = sitk.ImageRegistrationMethod()
        # Similarity metric settings.
        registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
        registration_method.SetMetricSamplingPercentage(0.03)
        registration_method.SetInterpolator(sitk.sitkLinear)
        # Optimizer settings.
        registration_method.SetOptimizerAsGradientDescent(learningRate=1.0,
                                                          numberOfIterations=300,
                                                          convergenceMinimumValue=1e-6,
                                                          convergenceWindowSize=10)
        registration_method.SetOptimizerScalesFromPhysicalShift()
        # Don't optimize in-place, we would possibly like to run this cell multiple times.
        registration_method.SetInitialTransform(initial_transform, inPlace=False)
        final_transform = registration_method.Execute(fixed_itk, moving_itk)
        # Check the reason optimization terminated.
        print('Final metric value: {0}'.format(registration_method.GetMetricValue()))
        print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
        # Write to file
        moving_resampled = sitk.Resample(moving_itk, fixed_itk,
                                               final_transform, sitk.sitkLinear, 0.0,
                                               moving_itk.GetPixelID())
        self._registered_image= sitk.GetArrayFromImage(moving_resampled)

        if save_path:
            save_path = Path(save_path)
            save_dir = save_path.parents[0]
            if not os.path.exists(save_dir):
                os.mkdir(save_dir)
            self.save(save_path)

        return moving_resampled

    def save(self, save_path):
        save_path = Path(save_path)
        save_dir = save_path.parents[0]
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        nifti_volume = nibabel.Nifti1Image(self._registered_image, np.eye(4))
        nifti_volume = self._resample(nifti_volume)
        nibabel.save(nifti_volume, save_path)

    def _resample(self, nifti_volume):
        nifti_volume = nibabel.processing.resample_to_output(nifti_volume, voxel_sizes=self._voxel_sizes)
        nifti_volume.header.set_zooms(self._voxel_sizes)
        nifti_volume.header.set_xyzt_units(xyz=self._voxel_unit)
        return nifti_volume

    def _resize(self, fixed_arr, moving_arr):
        (w1, h1, d1) = fixed_arr.shape
        moving_arr_resized = resize(moving_arr, (w1, h1, d1))
        return moving_arr_resized

