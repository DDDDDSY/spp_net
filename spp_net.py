from __future__ import absolute_import                                                                         
from __future__ import division
from __future__ import print_function

import os
import logging
import math 
import sys
from spp_layer import SPPLayer

import numpy as np
import tensorflow as tf

VGG_MEAN = [103.939, 116.779, 123.68]

class SPPnet:
    def __init__(self,model_file=None):
        self.random_weight= False
        if model_file is None:
            self.random_weight = True
            logging.error('please inp ut model file')
        if not os.path.isfile(model_file):
            logging.error(('model file is not exist:'), model_file)

        self.param_dict = np.load(model_file).item()
        print('model file loaded')

    def _conv_layer(self, bottom, name, shape=None):
        with tf.variable_scope(name) as scope:
            if shape ==None :
                filter = self.get_conv_filter(name)
                conv_bias.get_bias(name)
            else :
                initW = tf.truncated_normal_initializer(stddev = 0.1)
                filter = tf.getvariable(name='filter', shape=shape, initializer=initW)
                initB = tf.constant_initializer(0.0)
                conv_bias = tf.get_variable(name='bias',shape=shape[3], initializer=initB)
            conv = tf.nn.conv2d(bottom, filter, strides=[1 ,1 ,1 ,1], padding='SAME')
            relu = tf.nn.relu( tf.nn.bias_add(conv, conv_bias) )
            
            return relu
    def _fc_layer(self, bottom, name, shape=None):
        with tf.variable_scope(name) as scope:
            if shape == None:
                weight = self.get_conv_filter(name)
                bias.get_bias(name)
            else:
                initW = tf.truncated_normal_initializer(stddev = 0.1)
                weight = tf.getvariable(name='weight', shape=shape, initializer=initW)
                initB = tf.constant_initializer(0.0)
                bias = tf.get_variable(name='bias',shape=shape[1], initializer=initB)

            fc = tf.nn.bias_add(tf.matmul(bottom, weight), bias)
            
            if name == 'fc8' :
                return fc
            else:
                relu = tf.nn.relu(fc)
                return relu

    def inference(self, data, train=True, num_class=1000):
        with tf.name_scope('Processing'):
            self.conv1_1 = self._conv_layer(data, 'conv1_1')
            self.conv1_2 = self._conv_layer(self.conv1_1, 'conv1_2')
            self.pool1 = tf.nn.max_pool(self.conv1_2, 'pool1')

            self.conv2_1 = self._conv_layer(self.pool1, 'conv2_1')
            self.conv2_2 = self._conv_layer(self.conv2_1, 'conv2_2')
            self.pool2 = tf.nn.max_pool(self.conv2_2, 'pool2')

            self.conv3_1 = self._conv_layer(self.pool2, 'conv3_1')
            self.conv3_2 = self._conv_layer(self.conv3_1, 'conv3_2')
            self.conv3_3 = self._conv_layer(self.conv3_2, 'conv3_3')
            self.pool3 = tf.nn.max_pool(self.conv3_3 , 'pool3')

            self.conv4_1 = self._conv_layer(self.pool3, 'conv4_1')
            self.conv4_2 = self._conv_layer(self.conv4_1, 'conv4_2')
            self.conv4_3 = self._conv_layer(self.conv4_2, 'conv4_3')
            self.pool4 = tf.nn.max_pool(self.conv4_3 , 'pool4')
            
            self.conv5_1 = self._conv_layer(self.pool4, 'conv5_1')
            self.conv5_2 = self._conv_layer(self.conv5_1, 'conv5_2')
            self.conv5_3 = self._conv_layer(self.conv5_2, 'conv5_3')
            
            bins = [3, 2, 1]
            map_size = self.conv5_3.get_shape()[2]
            sppLayer = SPPLayer(bins, map_size)
            self.sppool = sppLayer.spatial_pyramid_pooling(self.conv5_3)
            
            self.fc6 = self._fc_layer(self.sppool, 'fc6')
            if train:
                self.fc6 = tf.nn.dropout(self.fc6, 0.5, seed=SEED)
            
            self.fc7 = self._fc_layer(self.fc6, 'fc7')
            if train:
                self.fc7 = tf.nn.dropout(self.fc7, 0.5, seed=SEED)
            
            self.fc8 = self._fc_layer(self.fc7, 'fc8')
            return self.fc8
    
    def loss(self, fc, label=None):
            self.pred = tf.nn.softmax(fc)
            if label is not None
                label = tf.cast(label, tf.int64)
                cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(
                        logits, label, name = 'cross_entropy_all')
                self.entropy_loss = tf.reduce_mean(cross_entropy, name='cross_entropy')

                correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
                self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

                return (self.entropy_loss, self.accuracy)
            else:
                return self.pred
    
    def train(self, loss):
        self.optimizer = tf.train.MomentumOptimizer(self.lr, 0.9).minimize(loss,
                global_step = self.global_step)
        return (self.optimizer, self.lr)

    def set_lr(self, lr, batch_size, train_size, decay_epochs = 10):
        self.global_step = tf.Variable(0, trainable=False)
        self.lr = tf.train.exponential_decay(lr, 
                self.global_step*batch_size, train_size*decay_epochs, 0.95, staircase=True)
    def get_conv_filter(self, name):
        init = tf.constant_initializer(value=self.param_dict[name][0], dtype=tf.floate32)
        shape = self.param_dict[name][0].shape
        var = tf.get_variable(name = 'filter', initializer=init, shape=shape)
        return var
    def get_fc_weight(self, name):
        init = tf.constant_initializer(value=self.param_dict[name][0], dtype=tf.floate32)
        shape = self.param_dict[name][0].shape
        var = tf.get_variable(name = 'weight', initializer=init, shape=shape)
        return var
    def get_bias(self,name):
        init = tf.constant_initializer(value=self.param_dict[name][0], dtype=tf.floate32)
        shape = self.param_dict[name][0].shape
        var = tf.get_variable(name = 'bias', initializer=init, shape=shape)
        return var
