# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import torch
# import data
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import sparseconvnet as scn
import time
import os, sys
import math
import numpy as np
import _pickle as pkl
import numpy as np
import pandas as pd
import glob
import pickle
from datetime import datetime

# data.init(-1,24,24*8,16)
model_data = pd.read_pickle("/home/dhai1729/small_model_20190304-180018_.pkl")
sz = model_data['sz']
spatialSize = model_data['spatialSize']
dimension = 3
reps = model_data['reps']
m = model_data['m']
nPlanes = model_data['nPlanes']
classes_total = 2 # Total number of classes
sampling_factor = model_data['sampling_factor']
features = model_data['features'] ## Choices: 'ring', 'z', 'const_vec', 'inten'
num_features = len(features)
norm_fact = model_data['norm_fact']

## Facebook's standard network
class Model(nn.Module):
    def __init__(self):
        nn.Module.__init__(self)
        self.sparseModel = scn.Sequential().add(
           scn.InputLayer(dimension, spatialSize, mode=3)).add(
           scn.SubmanifoldConvolution(dimension, num_features, m, 3, False)).add(
           scn.UNet(dimension, reps, nPlanes, residual_blocks=False, downsample=[2,2])).add(
           scn.BatchNormReLU(m)).add(
           scn.OutputLayer(dimension))
        self.linear = nn.Linear(m, classes_total)
    def forward(self,x):
        x=self.sparseModel(x)
        x=self.linear(x)
        return x

## Loading the model
model = torch.load('/home/dhai1729/road_segmentation.model')
print("Model loaded!")

# ## Class for data loading, training and testing

# class train_road_segmentation():
#     def __init__(self, train_path, test_path, train_mode, test_mode,  model, criterion, features, thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]):

#         ### loading the data and all into the os
#         self.train_path = train_path
#         self.test_path = test_path

#         ### getting list of the data
#         self.train_data_list = []
#         self.test_data_list = []
    
#         for i in range(len(self.train_path)):
#             self.train_data_list.extend(glob.glob(self.train_path[i] + '/*.pkl'))

#         for i in range(len(self.test_path)):
#             self.test_data_list.extend(glob.glob(self.test_path[i] + '/*.pkl'))


#         ### Number of inputs 
#         self.train_data_length = len(self.train_data_list)
#         self.test_data_length = len(self.test_data_list)

#         ### Getting train and test data in random order
#         self.train_indices = np.random.permutation(np.arange(self.train_data_length))
#         self.test_indices = np.random.permutation(np.arange(self.test_data_length))

#         ### Defining criterion for the neural network
#         self.criterion = criterion

#         ### Sparsenet model
#         self.model = model

#         ## Features to be used
#         self.use_features = features
        
#         ### Learning algorithm parameters
#         ### Learning params
#         self.p = {}
#         self.p['n_epochs'] = 12
#         self.p['initial_lr'] = 2e-1
#         self.p['lr_decay'] = 1e-1
#         self.p['weight_decay'] = 1e-2   
#         self.p['momentum'] = 0.9
#         # p['check_point'] = False
#         self.p['use_cuda'] = torch.cuda.is_available()
#         dtype = 'torch.cuda.FloatTensor' if self.p['use_cuda'] else 'torch.FloatTensor'
#         dtypei = 'torch.cuda.LongTensor' if self.p['use_cuda'] else 'torch.LongTensor'

#         ## IF GPU is available
#         if self.p['use_cuda']:
#             self.model = self.model.cuda()
#             self.model = nn.DataParallel(model)
#             self.criterion = self.criterion.cuda()

#         ### Training data variables
#         self.coords = None
#         self.features = None
#         self.train_output = None

#         ### Optimizer(Defined in training)
#         ### Optimizer(Defined in training)
#         self.optimizer = None

#         ### Precision, recall thresholds
#         self.thresholds = thresholds

#         ### Probability values
#         self.ps = None

#         ### Precision recall for each point cloud
#         self.precision = None
#         self.recall = None
#         self.accuracy = None
#         self.f1_score = None
#         self.classes = None
#         self.pred_labels = None

#         ## confusion matrix
#         self.confusion_m = None

#         ### To compute average time of forward pass
#         self.time_taken = [];

#     ### Normalizes the input data and samples points
#     def normalize_input(self, df):

#         ### Getting coordinates and features
#         x = df.iloc[0]['scan_utm']['x'] 
#         y = df.iloc[0]['scan_utm']['y']
#         z = df.iloc[0]['scan_utm']['z'] 

#         ### getting coordinate values between 0 and 150
#         x -= min(x)
#         y -= min(y)
#         z -= min(z)
#         x = norm_fact*x/max(x)
#         y = norm_fact*y/max(y) 
#         z = norm_fact*z/max(z) 

#         ### sampling every n th point as point cloud has more than 0.1 million points
#         n = sampling_factor
#         x = x[0::n]
#         y = y[0::n]
#         z = z[0::n]

#         ### Normalizing features?? Not decided yet

#         ### final train and test data
#         self.coords = torch.randn(len(x), dimension)
#         self.coords[:,0] = torch.from_numpy(x.copy())
#         self.coords[:,1] = torch.from_numpy(y.copy())
#         self.coords[:,2] = torch.from_numpy(z.copy())

#         ### Getting sampled features
#         self.features = torch.randn(len(x), len(self.use_features))
#         inten = df.iloc[0]['scan_utm']['intensity']
#         inten = inten.astype('float32')
#         inten = inten[0::n]
#         ring = df.iloc[0]['scan_utm']['ring']
#         ring = ring.astype('float32')
#         ring = ring[0::n]
#         const_vec = ring*0 + 127
#         features_dict = {'ring':ring, 'z':z, 'inten':inten, 'const_vec':const_vec}

#         for i in range(len(self.use_features)):
#             self.features[:,i] = torch.from_numpy(features_dict[self.use_features[i]].reshape(len(x),).copy())
#         #print("self.features.shape is: ", self.features.shape)
#         #self.features[:,0] = torch.from_numpy(features1.copy())
#         #self.features[:,0] = torch.from_numpy(features2.copy())
#         #self.features[:,1] = torch.from_numpy(features3.copy())
#         #self.features = self.features.astype('float32')
#         #features2 = features2.astype('float32')
#         #self.features[:,1] = torch.from_numpy(features1.copy())
#         #self.features.resize_(len(self.features), 1)
#         #self.features = self.features*0 + 127
#         #print(self.features)
#         del x, y, z

#         ## Getting the ground truth at every sample
#         self.train_output = 1*(df.iloc[0]['is_road_truth'] == True)
#         self.train_output = self.train_output[0::n]
#         self.train_output = torch.from_numpy(self.train_output.copy())
#         #self.train_output = self.train_output.resize_(len(self.train_output), 1)

#     def train_model(self):
        
#         ### Learning params
#         self.p['n_epochs'] = 10
#         self.p['initial_lr'] = 1e-1
#         self.p['lr_decay'] = 4e-2
#         self.p['weight_decay'] = 1e-5
#         self.p['momentum'] = 0.9

#         # p['check_point'] = False
#         self.p['use_cuda'] = torch.cuda.is_available()
#         dtype = 'torch.cuda.FloatTensor' if self.p['use_cuda'] else 'torch.FloatTensor'
#         dtypei = 'torch.cuda.LongTensor' if self.p['use_cuda'] else 'torch.LongTensor'

#         ## IF GPU is available
#         if self.p['use_cuda']:
#             self.model = self.model.cuda()
#             self.model = nn.DataParallel(model)
#             self.criterion = self.criterion.cuda()

#         ### Defining an optimizer for training
#         self.optimizer = optim.SGD(self.model.parameters(),
#             lr=self.p['initial_lr'],
#             momentum = self.p['momentum'],
#             weight_decay = self.p['weight_decay'],
#             nesterov=True)

#         ### Let's start training
#         for epoch in range(self.p['n_epochs']):

#             running_loss = 0

#             ### Model in a train mode
#             self.model.train()
#             # stats = {}


#             ### Don't know what this is happening!
#             for param_group in self.optimizer.param_groups:
#                 param_group['lr'] = self.p['initial_lr'] * math.exp((1 - epoch) * self.p['lr_decay'])
#             scn.forward_pass_multiplyAdd_count=0
#             scn.forward_pass_hidden_states=0
#             start = time.time()

#             ### let's start the training
#             ### iterating through the dataset and training
            
#             steps = 0
#             print("Training on ", len(self.train_indices), " point clouds.")
#             for i in self.train_indices:

#                 ## Keeping count of how many data points are loaded
#                 steps+=1 
#                 #if steps%100 == 0: 
#                 #print("At step: ", steps)

#                 ## let's load the data
#                 df = pd.read_pickle(self.train_data_list[i])

#                 ## Prepare data for training
#                 self.normalize_input(df)
#                 # break
#                 self.optimizer.zero_grad()

#                 ## Converting input into cuda  tensor if GPU is available
#                 self.coords = self.coords.type(torch.LongTensor)
#                 self.features=self.features.type(dtype)
#                 self.train_output=self.train_output.type(dtypei)

#                 ## Forward pass
#                 predictions=self.model((self.coords, self.features))
#                 # print(predictions.max(), predictions.min())

#                 ## Computing loss
#                 loss = self.criterion.forward(predictions,self.train_output)
#                 # print("Reached backward pass")

#                 ## backprop into the loss to compute gradients
#                 loss.backward()

#                 ## Updating weights
#                 self.optimizer.step()

#                 ## Calculating running loss
#                 running_loss+= loss.item()
            
#             print("Epoch: {}/{}... ".format(epoch+1, self.p['n_epochs']), "Loss: {:.4f}", running_loss/len(self.train_indices))        

#             if (epoch)%5==0:
#                 self.test_model()

#     def test_model(self):

#         steps = 0
        
#         self.model.eval()

#         dtype = 'torch.cuda.FloatTensor' if self.p['use_cuda'] else 'torch.FloatTensor'
#         dtypei = 'torch.cuda.LongTensor' if self.p['use_cuda'] else 'torch.LongTensor'
#         ## This has total number of true pixels for all the pointclouds being tested
#         true_predictions = 0
#         ## Total number of points processed across all the pointclouds being tested
#         total_points = 0
#         ## Let's test for entire test set
#         bad_acc_pointclouds = 0   ## number of pointclouds with bad accuracy
    

#         print("Testing on: ", len(self.test_indices), "point clouds.")
#         lowest_acc = 200
#         highest_acc = 10
#         for i in self.test_indices:

#             ## Keeping count of how many data points are loaded
#             steps+=1 
#             #print("At step: ", steps)

#             ## let's load the data
#             df = pd.read_pickle(self.test_data_list[i])

#             ## Prepare data for training
#             self.normalize_input(df)
                
#             ## Converting input into cuda  tensor if GPU is available
#             self.coords = self.coords.type(torch.LongTensor)
#             self.features=self.features.type(dtype)
#             self.test_output=self.train_output.type(torch.FloatTensor) ### To compute accuracy
#             with torch.no_grad():
#                 ## Forward pass
#                 t = time.time()
#                 predictions=self.model((self.coords, self.features))        
#                 self.time_taken.append(time.time() - t)


#             ## Softmax  
#             self.ps = F.softmax(predictions, dim=1)
#             #index = np.where(self.ps[:,1].cpu().numpy()>0.4)
#             #index = torch.zeros(self.ps.shape[0], 1)
#             values, index = self.ps.max(dim = 1)
#             index = index.type(torch.FloatTensor)
#             accuracy = 100*(np.count_nonzero((index - self.test_output).numpy()==0)/len(index))
#             #print("Accuracy for point cloud ", i, " is: ", accuracy, "%.")
#             if accuracy < 90:
#                 bad_acc_pointclouds +=1
#             if accuracy < lowest_acc:
#                 lowest_acc = accuracy
#             if accuracy > highest_acc:
#                 highest_acc = accuracy
#             true_predictions+= np.count_nonzero((index - self.test_output).numpy()==0)
#             total_points+=len(index)

#         overall_accuracy = true_predictions/total_points
#         print(bad_acc_pointclouds, " point clouds have accuracy less than 90.")
#         print("Average time for forward pass is: ", np.mean(np.array(self.time_taken)))
#         print("Total accuracy is: ", overall_accuracy*100)
#         print("Lowest accuracy is: ", lowest_acc)
#         print("Highest accuracy is: ", highest_acc)
#         bad_acc_pointclouds = 0
#         self.time_taken = []

#     def test_single_cloud(self, path):
#         ## testing a single point cloud and generating statistics
#         self.model.eval()

#         ## Datatype based on GPU availability
#         dtype = 'torch.cuda.FloatTensor' if self.p['use_cuda'] else 'torch.FloatTensor'
#         dtypei = 'torch.cuda.LongTensor' if self.p['use_cuda'] else 'torch.LongTensor'

#         ## Loading the point cloud
#         df = pd.read_pickle(path)
        
#         ## Prepare data for training
#         self.normalize_input(df)
            
#         ## Converting input into cuda  tensor if GPU is available
#         self.coords = self.coords.type(torch.LongTensor)
#         self.features=self.features.type(dtype)
#         self.test_output=self.train_output.numpy() #.type(torch.FloatTensor) ### To compute accuracy
#         with torch.no_grad():
#             ## Forward pass
#             predictions=self.model((self.coords, self.features))        


#         ## Softmax
#         self.ps = F.softmax(predictions, dim=1)

#         ## let's compute confusion matrix and statistics
#         self.confusion()

#     ## Compute confusion matrix, precision, recall etc etc for a single pointcloud
#     def confusion(self):

#         ## precision and recall array for different thresholds
#         self.precision = []
#         self.recall = []
#         self.f1_score = []
#         self.accuracy = []
#         for thresh in self.thresholds:
#             ## create prediction vector
#             self.classes = np.where(self.ps[:,1].cpu().numpy()>thresh)
#             self.pred_labels = np.zeros(self.ps.shape[0])
#             self.pred_labels[self.classes] = 1

#             ## Create confusion matrix
#             self.confusion_m = np.bincount(self.pred_labels.astype(int)*2+self.test_output.astype(int), minlength=4).reshape((2,2))
            
#             ## getting precision,recall from confusion matrix
#             tp = self.confusion_m[1,1]   ## True positive
#             tn = self.confusion_m[0,0]   ## True negative
#             fp = self.confusion_m[1,0]   ## False positive
#             fn = self.confusion_m[0,1]   ## False negative
#             print("tp, tn, fp, fn: ", tp, tn, fp, fn)
#             ## Saving precision and recall
#             self.precision.append(tp/(tp+fp))
#             self.recall.append(tp/(tp+fn))
#             self.f1_score.append(2*self.precision[-1]*self.recall[-1]/(self.precision[-1] + self.recall[-1]))
#             self.accuracy.append((tp+tn)/self.ps.shape[0])



#     ## Let's compute the confusion matrix.
#     ## This saves train and test indices, model, accuracy and other necessary information for future usage
#     # def save_variables(self):
#     #     ## To be written in future



# ## Let's start here! 

# # model = Model()
# str_date_time = datetime.now().strftime('%Y%m%d-%H%M%S')
# print("Model is created!")
# ## Criterion for the loss
# criterion = nn.CrossEntropyLoss()
# train_path = ['/home/dhai1729/scratch/maplite_data/data_chunks/','/home/dhai1729/scratch/maplite_data/truth_snow_500', '/home/dhai1729/scratch/maplite_data/truth_500_2018-09-09-16-21-52']
# test_path = ['/home/dhai1729/scratch/maplite_data/truth_500_2019-01-25-14-31-55', '/home/dhai1729/scratch/maplite_data/truth_snow_500_2'] 
# train_mode = True
# test_mode = True
# ## Creating object(refine this once it works)
# trainobj = train_road_segmentation(train_path, test_path, train_mode, test_mode, model, criterion, features, thresholds = np.arange(0.05,1.0,0.05))
# print("About to go in training.")
# trainobj.train_model()
# ## Time to save all the necessary variables

# ## Dictionary to be saved!
# final_data = {'train_path':train_path,
#               'test_path': test_path,
#               'sz': sz,
#               'spatialSize': spatialSize,
#               'reps': reps,
#               'm':m,
#               'norm_fact':norm_fact,
#               'sampling_factor': sampling_factor,
#               'learning_params': trainobj.p,
#               'features': features,
#               'nPlanes': nPlanes}
# f = open('/home/dhai1729/small_model_' + str_date_time + '_.pkl', 'wb')
# pickle.dump(final_data, f)
# #pickle.dump([train_mode, test_mode, sz, spatialSize, reps, m, norm_fact, sampling_factor, trainobj.p, features], f)
# f.close()
# torch.save(trainobj.model, '/home/dhai1729/small_model_' + str_date_time + '_.model')    


