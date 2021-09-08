# brain_preprocessing

## Installing the dependencies

1. Python dependencies can be installed via the dependency file **requirements.txt**
    ```
    pip install -r requirements.txt
    ```

## CLI

This CLI application takes 4 structural brain MRIs (t1, t2, flair, t1ce) as input (can be either in nifti format or dicom).

```
python ./src/pipeline.py -h
```

### Taking nifti files as input
```
python ./src/pipeline.py -t1 path/to/t1.nii.gz -t2 path/to/t2.nii.gz -fl path/to/flair.nii.gz -t1ce path/to/t1ce.nii.gz -o path/to/output/folder
```

### Taking dicom folders as input 
```
python ./src/pipeline.py -t1 path/to/t1/dicom/folder -t2 path/to/t2/dicom/folder -fl path/to/t1/flair/folder -t1ce path/to/t1ce/dicom/folder -o path/to/output/folder
```

