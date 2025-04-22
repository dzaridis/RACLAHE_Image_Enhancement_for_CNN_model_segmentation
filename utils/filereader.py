import os
import SimpleITK as sitk
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import generate_uid
import pydicom

class MedicalImageReader:
    def __init__(self, directory):
        self.directory = directory

    def read_image(self):
        if self._contains_nifti_files():
            return self._read_nifti_file()
        elif self._contains_dicom_files():
            return self._read_dicom_series()
        else:
            raise ValueError("The directory does not contain NIfTI or DICOM files.")

    def _contains_nifti_files(self):
        return any(file.endswith('.nii') or file.endswith('.nii.gz') for file in os.listdir(self.directory))

    def _contains_dicom_files(self):
        return any(file.lower().endswith('.dcm') for file in os.listdir(self.directory))

    def _read_nifti_file(self):
        nifti_files = [file for file in os.listdir(self.directory) if file.endswith('.nii') or file.endswith('.nii.gz')]
        if len(nifti_files) != 1:
            raise ValueError("More than one NIfTI file found. Unsure which one to read.")
        return sitk.ReadImage(os.path.join(self.directory, nifti_files[0]))

    def _read_dicom_series(self):
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(self.directory)
        reader.SetFileNames(dicom_names)
        return reader.Execute()

class dicom_save:

    def __init__(self, original_series_directory, processed_image, output_directory) -> None:
        self.original_series_directory= original_series_directory
        self.processed_image = processed_image
        self.output_directory = output_directory
        
    @staticmethod
    def copy_dicom_metadata(original_dicom, new_dicom):
        # Copy relevant fields from the original DICOM file
        for elem in original_dicom:
            if elem.tag.is_private:
                continue  # Skip private tags
            new_dicom.add(elem)
            
        new_dicom.is_little_endian = original_dicom.is_little_endian
        new_dicom.is_implicit_VR = original_dicom.is_implicit_VR
        return new_dicom

    def save_as_dicom_series(self):
        dicom_files = [f for f in os.listdir(self.original_series_directory) if f.endswith('.dcm')]
        dicom_files.sort()  # Sorting may be necessary for correct slice order

        # Ensure the output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
        k =sitk.GetArrayFromImage(self.processed_image)
        # Iterate over each slice in the processed image
        for i in range(k.shape[0]):  # Assuming the first dimension is the slice dimension
            # Extract the i-th slice
            slice_2d = k[i, :, :]

            # Read the corresponding original DICOM file
            original_dicom = pydicom.dcmread(os.path.join(self.original_series_directory, dicom_files[i]))

            # Create a new DICOM file copying the original metadata
            new_dicom = Dataset()
            new_dicom = self.copy_dicom_metadata(original_dicom, new_dicom)

            # Set pixel data to the processed image slice
            new_dicom.PixelData = slice_2d.tobytes()

            # Update specific metadata fields if necessary
            new_dicom.SOPInstanceUID = generate_uid()
            new_dicom.InstanceNumber = str(i + 1)

            # Save the new DICOM file
            new_dicom.save_as(os.path.join(self.output_directory, f"image_{i + 1}.dcm"))