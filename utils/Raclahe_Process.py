#!/usr/bin/env python
# coding: utf-8

# In[79]:


import numpy as np, pandas as pd, pydicom as dcm, os
import nibabel as nib
import SimpleITK as sitk
from glob import glob
from keras_unet_collection._model_unet_2d import unet_2d
import cv2 as cv
os.environ['GIT_PYTHON_REFRESH'] = "quiet"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import numpy as np
from skimage.exposure import equalize_adapthist
import time
from filereader import *

    
    
def bounding_box_prediction_and_cropping(weights_path,patients):
    """ Predicts the bounding box of the area of interest
    Args:
        weights_path(str path\.h5): The path where the weights of the trained unet model are onto
        patients(3D np.array(Slice,Width,Height)):Numpy array containing all the patients , Min-Max normalization, 256x256 frame dimensions
    Returns:
        pat_box(4D np.array,[patient,slice,Width,Height]): returns the predicted bounding box masks from the tool
    """

    filters=[32, 64, 128, 256, 512, 1024]
    model=unet_2d((256,256,1), filters, 1, stack_num_down=2, stack_num_up=2,
            activation='ReLU', output_activation='Sigmoid', batch_norm=True, pool=True, unpool=True, 
            backbone=None, weights=None, freeze_backbone=True, freeze_batch_norm=True, name='unet')
    model.load_weights(weights_path)

    pat_coords=[]
    slice_xmax,slice_ymax,slice_xmin,slice_ymin=[],[],[],[]
    data=tf.expand_dims(patients,axis=3)
    all_coords=[]
    for i in range (data.shape[0]):
        try:
            prediction = model.predict(np.expand_dims(data[i],axis=0))
            prediction=np.squeeze(prediction,axis=0)
            prediction=np.squeeze(prediction,axis=2)
            for k in range (prediction.shape[0]):
                for l in range (prediction.shape[1]):
                    if prediction[k][l]<0.35:
                        prediction[k][l]=0
            crd = np.column_stack(np.where(prediction > 0))

            
            xmax,ymax = np.max(crd,axis=0) 
            xmin,ymin = np.min(crd,axis=0)

            #pred_coordinates[i][0],pred_coordinates[i][1],pred_coordinates[i][2],pred_coordinates[i][3]=xmax,ymax,xmin,ymin
            slice_xmax.append(xmax)
            slice_ymax.append(ymax)
            slice_xmin.append(xmin)
            slice_ymin.append(ymin)
            all_coords.append({"x-max":xmax,"y-max":ymax,"x-min":xmin,"y-min":ymin})
            
        except: #ValueError:  #raised if `y` is empty.
            slice_xmax.append(data[i].shape[1])
            slice_ymax.append(data[i].shape[2])
            slice_xmin.append(0)
            slice_ymin.append(0)
            all_coords.append({"x-max":data[i].shape[1],"y-max":data[i].shape[2],"x-min":0,"y-min":0})
            
    slice_xmax=np.asarray(slice_xmax)
    slice_ymax=np.asarray(slice_ymax)
    slice_xmin=np.asarray(slice_xmin)
    slice_ymin=np.asarray(slice_ymin)
    
    pat_coords.append([slice_xmax,slice_ymax,slice_xmin,slice_ymin])
        
    pat_coords=np.asarray(pat_coords)
    #try:
    box=[]
    for i in range(patients.shape[0]):
        b_b=np.zeros(patients[i].shape)
        b_b[pat_coords[0][2][i]:pat_coords[0][0][i],pat_coords[0][3][i]:pat_coords[0][1][i]]=1
        box.append(b_b)
    box_cr=np.asarray(box)
    #for i in range (data_cr.shape[0]):
        #plt.imsave(r"C:\Users\elena\Desktop\Dimitris-Deep learning\Prostate-x\BOUND_BOX_PIPELINE\cropped\Image_cr_{}.png".format(i),data_cr[i],cmap="gray")
        #plt.imsave(r"C:\Users\elena\Desktop\Dimitris-Deep learning\Prostate-x\BOUND_BOX_PIPELINE\cropped\Labels_cr_{}.png".format(i),labels_cr[i],cmap="gray")

    return box_cr,all_coords


# In[12]:


def apply_square_filter(pats_sf,bounding,mask):
    """
    Args:
        patients (np.array): patients 4d (patient,slice,width,height)
        bounding(square mask np.array): bounding box
        mask: whether to choose area inside or outside the mask 0-1:0 inside the mask,1 outside
    Returns:
        patients excluding information from the area of the mask
    """
    patients=np.copy(pats_sf)
    frames_square_filter=[]
    for j in range(patients.shape[0]):
        coords=np.where(bounding[j]==mask)
        for k,l in zip(coords[0],coords[1]):
            frame_sq_f=patients[j]
            frame_sq_f[k,l]=0
        frames_square_filter.append(frame_sq_f)
    frames_square_filter=np.asarray(frames_square_filter)  

    return(frames_square_filter)


# In[13]:


def adapt_hist_apply(pats):
    """ applies the filter on 3d np array
    Args:
        patients(3d np.array[slice,width,height]): patients array
    Returns:
        new_patient(3d np.array): The filtered patient
        times_passed: returns the time needed to process 1 patient
    """
    patients=np.copy(pats)
    sl=[]
    sl_an=[]
    start_time_pat=time.time()
    times_passed=[]
    for i in range(patients.shape[0]):
        start_time_sl=time.time()
        sl.append((equalize_adapthist(patients[i])))#canny patients[j][i] (binary_fill_holes canny,simga=3)
        #print("Slice {:}".format(i),"took",time.time()-start_time_sl," seconds")
        times_passed.append(time.time()-start_time_sl)
    sl=np.asarray(sl)
    return(sl,times_passed)


# In[9]:

def prepro(sls):

    sl_pre=[]
    for j in range(sls.shape[0]):
        sl_pre.append(cv.resize(sls[j], (256,256),cv.INTER_LINEAR))
    sl_pre=np.asarray(sl_pre)
    
    sl_std=[]
    for j in range(sl_pre.shape[0]):
        sl_std.append((sl_pre[j]-np.min(sl_pre[j]))/(np.max(sl_pre[j])-np.min(sl_pre[j])))
    sl_std=np.asarray(sl_std)    
 
    return(sl_std)

def roi_focus(d,weights_path,identity_patient):
    """
    Applies the raclahe method
    Args:
        d (4D np.array [Patients, Slices, Width, height]): The min-max(intensity range:[0,1]) standardized patients
        weights_path(str path\.h5): The path where the weights of the bounding boxtrained unet model are onto
    Returns:
        the raclahe enhanced patients(4D np.array [Patients, Slices, Width, height])
        the bbox mask created for each slice and patient (4D np.array [Patients, Slices, Width, height])
    """

    pre_slices=prepro(d)
        
    sl_all=[]
    for j in range(pre_slices.shape[0]):
        it=np.copy(pre_slices[j])
        sl_all.append(it)
    sl_all=np.asarray(sl_all)

    bbox,coords=bounding_box_prediction_and_cropping(weights_path,sl_all)
    try:
        focused_pats=apply_square_filter(sl_all,bbox,0)
        
        sl_all=[]
        for j in range(pre_slices.shape[0]):
            it=np.copy(pre_slices[j])
            sl_all.append(it)
        sl_all=np.asarray(sl_all)

        unfocused_pats=apply_square_filter(sl_all,bbox,1)
        lapl_pats=adapt_hist_apply(np.copy(focused_pats))[0]
        
        
        cl_fr=[]
        for j in range (lapl_pats.shape[0]):
            cl_fr.append(lapl_pats[j]+unfocused_pats[j])
        cl_fr=np.asarray(cl_fr)
    except:
        cl_fr=sl_all
        print("Patient",identity_patient, "Didn't work")
        
    return cl_fr,bbox,coords

def Raclahe_process_nifti(pat,w_p,patient,user_output, user_input):
    """
    Raclahe pipeline
    Args:
        pat (4D np.array [Patients, Slices, Width, height]): The min-max(intensity range:[0,1]) standardized patients
        zone:0 or 1 or 2 for Whole gland, Transitional, Peripheral zones respectively
    Returns:
        the raclahe enhanced patients(4D np.array [Patients, Slices, Width, height])
        the bbox mask created for each slice and patient (4D np.array [Patients, Slices, Width, height])
    """

    
     #inp=str(input())
    inp=pat
    #pth = os.path.join(user_input, inp)
    #print("Creating of output directory")
    try:
        os.mkdir(os.path.join(user_output,"RACLAHE OUTPUT"))
    except:# FileExistsError:
       # print("RACLAHE OUTPUT directory already exists")
        pass
    out_pth=os.path.join(user_output,"RACLAHE OUTPUT")
    p_s=[]
    mt_data=[]
    #path_pat=os.listdir(pth)
    
    #nif_pth=os.path.join(pth,path_pat[0])
    #series=nib.load(user_input)
    #imgs=series.get_data()
    imgs = sitk.GetArrayFromImage(patient)
    try:
        assert (imgs.shape[0]<imgs.shape[1] and imgs.shape[0]<imgs.shape[2])
    except AssertionError:
        imgs=np.transpose(imgs, axes=(2,1,0))
    
    Raclahe_Enhanced_patients,proposed_box,coords = roi_focus(imgs,w_p,pat)
    image = sitk.GetImageFromArray(Raclahe_Enhanced_patients)
    #out_pth=os.path.join(out_pth,inp)
    dicts=[]
    identity={}
    #Raclahe_Enhanced_patients=np.transpose(Raclahe_Enhanced_patients,axes=(2,1,0))
    #assert (Raclahe_Enhanced_patients.shape[2]<Raclahe_Enhanced_patients.shape[0] and Raclahe_Enhanced_patients.shape[2]<Raclahe_Enhanced_patients.shape[1])
    try:
        l = dicom_save(user_input, image, os.path.join(out_pth,"{}".format(inp)))
        l.save_as_dicom_series()
        print(f"{pat} dicom saved succesfully")
    except IndexError:
        image.SetSpacing(patient.GetSpacing())
        image.SetOrigin(patient.GetOrigin())
        image.SetDirection(patient.GetDirection())
        try:
            os.mkdir(os.path.join(out_pth, inp))
        except:# FileExistsError:
       # print("RACLAHE OUTPUT directory already exists")
            pass
        to_save = os.path.join(out_pth, inp)
        sitk.WriteImage(image, os.path.join(to_save,"{}.nii.gz".format(inp)))
        print(f"{pat} nifti saved succesfully")
    except:
        np.save(os.path.join(out_pth,"{}.npz".format(inp)),Raclahe_Enhanced_patients)
    #another_image=nib.Nifti1Image(Raclahe_Enhanced_patients, series.affine, series.header)
    #nib.save(another_image, os.path.join(out_pth,"{}".format(inp)))
    for i in range(len(coords)):
        identity.update({inp+"_Slice_{:02}".format(i):{"Enhanced Box":coords[i]}})
        

        #plt.imsave(out_pth+"\sl_{:02}.png".format(i), Raclahe_Enhanced_patients[i],cmap="gray")
    #return Raclahe_Enhanced_patients,proposed_box
    #print("Raclahe enhanced patient nifty file has been saved")
    return identity




