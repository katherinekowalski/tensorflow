# Lint as: python3
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# pylint: disable=g-bad-import-order

"""Load data from the specified paths and format them for training."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

import numpy as np
import tensorflow as tf

from data_augmentation import augment_data

LABEL_NAME = "gesture"
DATA_NAME = "accel_ms2_xyz"


class DataLoader(object):
  """Loads data and prepares for training."""

  def __init__(self, train_data_path, valid_data_path, test_data_path,
               seq_length):
    self.dim = 3
    self.seq_length = seq_length
    # self.label2id = {"A":0,"B":1,"C":2,"D":3,"E":4,"F":5,"G":6,"H":7,"I":8,"J":9,"K":10,"L":11,"M":12,"N":13,"O":14,
    #     "P":15,"Q":16,"R":17,"S":18,"T":19,"U":20,"V":21,"W":22,"X":23,"Y":24,"Z":25,
    #     "apostrophe":26,"backspace":27,"comma":28,"done":29,"exclamation_point":30, "period":31,
    #     "question_mark":32,"quotes":33,"slash":34,"space":35, "negative":36}
    self.label2id = {"A":0, "B":1, "N":2, "O":3, "backspace":4, "space":5, "done":6}

    self.train_data, self.train_label, self.train_len = self.get_data_file(
        train_data_path, "train")
    self.valid_data, self.valid_label, self.valid_len = self.get_data_file(
        valid_data_path, "valid")
    self.test_data, self.test_label, self.test_len = self.get_data_file(
        test_data_path, "test")

  def get_data_file(self, data_path, data_type):
    """Get train, valid and test data from files."""
    data = []
    label = []
    with open(data_path, "r") as f:
      lines = f.readlines()
      for idx, line in enumerate(lines):  # pylint: disable=unused-variable
        dic = json.loads(line)
        data.append(dic[DATA_NAME])
        label.append(dic[LABEL_NAME])
    # if data_type == "train":
    #   data, label = augment_data(data, label)
    length = len(label)
    print(data_type + "_data_length:" + str(length))
    return data, label, length

  def pad(self, data, seq_length, dim):
    """Get neighbour padding."""
    noise_level = 20
    padded_data = []
    # Before- Neighbour padding
    tmp_data = (np.random.rand(seq_length, dim) - 0.5) * noise_level + data[0]
    tmp_data[(seq_length -
              min(len(data), seq_length)):] = data[:min(len(data), seq_length)]
    padded_data.append(tmp_data)
    # After- Neighbour padding
    tmp_data = (np.random.rand(seq_length, dim) - 0.5) * noise_level + data[-1]
    tmp_data[:min(len(data), seq_length)] = data[:min(len(data), seq_length)]
    padded_data.append(tmp_data)
    return padded_data

  def format_support_func(self, padded_num, length, data, label):
    """Support function for format.(Helps format train, valid and test.)"""
    # Add 2 padding, initialize data and label
    length *= padded_num
    features = np.zeros((length, self.seq_length, self.dim))
    labels = np.zeros(length)
    # Get padding for train, valid and test
    for idx, (data, label) in enumerate(zip(data, label)):
      # padded_data = self.pad(data, self.seq_length, self.dim)
      for num in range(len(data)):
        features[idx] = data[num]
        labels[idx] = self.label2id[label]
    # Turn into tf.data.Dataset
    dataset = tf.data.Dataset.from_tensor_slices(
        (features, labels.astype("int32")))
    return length, dataset

  def format(self):
    """Format data(including padding, etc.) and get the dataset for the model."""
    padded_num = 1
    self.train_len, self.train_data = self.format_support_func(
        padded_num, self.train_len, self.train_data, self.train_label)
    self.valid_len, self.valid_data = self.format_support_func(
        padded_num, self.valid_len, self.valid_data, self.valid_label)
    self.test_len, self.test_data = self.format_support_func(
        padded_num, self.test_len, self.test_data, self.test_label)
