#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from keras_unet_collection._model_unet_2d import unet_2d
import tensorflow_addons as tfa
from tensorflow_addons.losses import SigmoidFocalCrossEntropy,sigmoid_focal_crossentropy
import os
class Bounding_Box_Preprocessing:
    """
    Creates an instance for normalization steps and takes as input a 3D numpy array with shape [slice,width,height]
     """
    def __init__(self,patients,labels):
        self.patients = patients
        self.labels = labels
        
    def norm8bit(self):
        np.seterr(all="ignore")
        """ Normalization of the patients as np.uint8 (Intensity scale from 0-255 integer values)
        Args:
            patients(4d np.array[Patient,slice,width,height]): patients array
        Returns:
            new_patient(4D np.array): Uint8 normalized patients (intensity scale from 0-255)
        """
        pats=[]
        for j in range(self.patients.shape[0]):
            mn = self.patients[j].min()
            mx = self.patients[j].max()
            mx -= mn
            pats.append((((self.patients[j] - mn)/mx) * 255).astype(np.uint8))
        pats=np.asarray(pats)
        return pats
    
    def Standardization(self,min_max=False):#4d array(patients,slices,width,height)
        """ Normalization of the images patient wised
        Args:
            self(3d np.array[slice,width,height]): slices array
            min_max(Boolean):True/False , true for min max scaler false for z-score
        Returns:
            new_patient(3D np.array): The standardized slices
        """
        np.seterr(all="ignore")
        if min_max==True:
            norm_patients=[]
            for slice in self.patients:
                norm=(slice-np.min(slice))/(np.max(slice)-np.min(slice))
                norm_patients.append(norm)
            norm_patients=np.asarray(norm_patients)
        else:
            scaler = StandardScaler()
            norm_patients=[]
            for slice in self.patients:
                scaler.fit(slice.reshape(-1,1))
                norm_patients.append(np.reshape(scaler.transform(slice.reshape(-1,1)),(slice.shape[0],slice.shape[1])))
            norm_patients=np.asarray(norm_patients)
        return norm_patients
    
    def resize(self,x,y,anno=True):
        """ Resize the patients to certain dimensions on width and height
        Args:
            self(3d np.array[slice,width,height]): slices array
            x:Width to resize
            y:Height to resize
            anno(Boolean):True/False if annotation/not (nearest neighbor if image, bilinear if annotation)
        Returns:
            processed_patients(3D np.array):resized slices
        """
        print("anno is :",anno)
        processed_patients=[]
        if anno==False:
            for slice in self.patients:
                processed_patients.append(cv.resize(slice, (x,y),cv.INTER_LINEAR))
                #processed_slice.append(cv.convertScaleAbs(slice, alpha=alpha, beta=beta))
            processed_patients=np.asarray(processed_patients)
            
        elif anno==True:
            for slice in self.labels:
                processed_patients.append(cv.resize(slice, (x,y),cv.INTER_NEAREST))
                #processed_slice.append(cv.convertScaleAbs(slice, alpha=alpha, beta=beta))
            processed_patients=np.asarray(processed_patients)

        return processed_patients 
    
    def bounding_box_creation(self, size,path,extract_bounding=False):   
        """ Creating The bounding box around the mask
        Args:
            clear_data(3D np.array,[slice,Width,Height]): input patient
            clear_labels(3D np.array,[slice,Width,Height]): input patient's mask
            size(integer):size to crop the bounding box from the mask
            path(string path):path to save the image with the ractangle which will be cropped upon
            extract_bounding(Boolean):Whether to save the image with the rectangle annotated on top
        Returns:
            cropped_images(3D np.array,[slice,Width,Height]):Cropped images of the patients on the rectangular
            cropped_labels(3D np.array,[slice,Width,Height]):A rectangular mask of the bounding box containing inside the area of interest
            sm:initial patient with the rectangular to crop on top
            b_box: The rectangular mask for the train process
        """
        sm=[]
        coordinates=[]
        for i in range(self.patients.shape[0]):
            img=self.patients[i]
            label=self.labels[i]
            coords = np.column_stack(np.where(label > 0))
            coordinates.append(coords)
            summed = np.empty([256,256], dtype=float) 
            for j in range(img.shape[0]):
                for k in range(img.shape[1]):
                    summed[j][k]=img[j][k] #+ (label[j][k]*255)
            sm.append(summed)    
            #print("the coords are",coords)
        coordinates=np.asarray(coordinates)
        coordinates.shape
        coords = np.empty([len(coordinates), 4])
        for i in range(len(coordinates)):
            xmax,ymax = np.max(coordinates[i][:][:],axis=0) 
            xmin,ymin = np.min(coordinates[i][:][:],axis=0)
            #print(xmin,xmax,ymin,ymax)
            xmin=xmin-size
            xmax=xmax+size
            ymin=ymin-size
            ymax=ymax+size
            coords[i][0],coords[i][1],coords[i][2],coords[i][3]= xmin, xmax, ymin, ymax
            sm[i]=cv.rectangle(sm[i], (ymin,xmin), (ymax,xmax), [1,1,1],thickness = 2)
            if extract_bounding:
                   plt.imsave(path+"\Image_{}.png".format(i),sm[i],cmap="gray")
        coords=coords.astype(int)
        cropped_images=list()
        for i in range(coords.shape[0]):
            cropped_images.append(self.patients[i][coords[i,0]:coords[i,1],coords[i,2]:coords[i,3]])
        cropped_images=np.asarray(cropped_images)
        cropped_labels=list()
        for i in range(coords.shape[0]):
            cropped_labels.append(self.labels[i][coords[i,0]:coords[i,1],coords[i,2]:coords[i,3]])
        cropped_labels=np.asarray(cropped_labels)

        b_box=list()
        for i in range(coords.shape[0]):
            cl_lb=np.zeros(self.labels[i].shape)
            cl_lb[coords[i,0]:coords[i,1],coords[i,2]:coords[i,3]]=1
            b_box.append(cl_lb)
        b_box=np.asarray(b_box)

        return cropped_images,cropped_labels,sm,b_box
    
def model_definition(img_size=(256,256,1),filters=[16,32,64,128,256,512,1024],output_activation='Sigmoid'):
    mdl_unet=unet_2d(img_size, filters, 1, stack_num_down=2, stack_num_up=2,
            activation='ReLU', output_activation='Sigmoid', batch_norm=True, pool=True, unpool=True, 
            backbone=None, weights=None, freeze_backbone=True, freeze_batch_norm=True, name='unet')
    model = mdl_unet
    initial_learning_rate = 0.0001
    lr_schedule = keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate, decay_steps=100000, decay_rate=0.96, staircase=True)

    model.compile(
    loss=sigmoid_focal_crossentropy, #SigmoidFocalCrossEntropy
    optimizer=keras.optimizers.Adam(learning_rate = initial_learning_rate),#lr_schedule
    metrics=["acc"])
    
    return model

def model_training(data_train,labels_train,data_val,labels_val,save_weights_path):
    
    data_train  =  tf.expand_dims(data_train,axis=3)
    labels_train=  tf.expand_dims(labels_train,axis=3)
    data_val    =  tf.expand_dims(data_val,axis=3)
    labels_val  =  tf.expand_dims(labels_val,axis=3)
    
    model = model_definition(img_size=(256,256,1),filters=[16,32,64,128,256,512,1024],output_activation='Sigmoid')

    bs=16
    epochs = 100
    
    checkpoint_cb = keras.callbacks.ModelCheckpoint(os.path.join(save_weights_path,"bbox_weights.h5"), save_best_only=True)
    tqdm_cb=tfa.callbacks.TQDMProgressBar()
    early_stopping_cb = keras.callbacks.EarlyStopping(monitor="val_loss", patience=6)

    model.fit(
    x=data_train,y=labels_train, #[data_train,data_train,data_train]
    validation_data=(data_val,labels_val), #[data_val,data_val,data_val]
    batch_size=bs,
    epochs=epochs,
    shuffle=True,
    verbose=0,
    callbacks=[checkpoint_cb,early_stopping_cb,tqdm_cb])

