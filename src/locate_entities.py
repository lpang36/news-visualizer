import sys
import requests
import os.path
import pickle
import re
from copy import copy
import numpy as np
import tensorflow as tf
import random
import math
from matplotlib import pylab
from sklearn.manifold import TSNE

def locate_entities():
  articles = []
  with open('../data/articles.pkl','rb') as f:
    articles = pickle.load(f)
    
  kws = []
  with open('../data/keywords.pkl','rb') as f:
    kws = pickle.load(f)
  kws_table = {}
  for i,t in enumerate(kws):
    for w in t[1:]:
      kws_table[w] = i  
  
  data = []
  for title,description,_ in articles:
    row = []
    for k in kws_table:
      temp = (title+description).lower()
      if ' '+k in temp or k+' ' in temp:
        if kws_table[k] not in row:
          row.append(kws_table[k])
    if len(row)>1:      
      data.append(row)
  with open('../data/entitydata.pkl','wb') as f:
    pickle.dump(data,f)
  
  def generate_batch(n,dat):
    temp = random.sample(dat,n)
    batch = [0]*len(temp)
    labels = [0]*len(temp)
    for i,t in enumerate(temp):
      batch[i],labels[i] = tuple(random.sample(t,2))
    return np.asarray(batch),np.reshape(np.asarray(labels),(-1,1))
  
  batch_size = 128
  embedding_size = 128
  vocabulary_size = max(kws_table.values())+1
  num_sampled = 64
  
  graph = tf.Graph()
  with graph.as_default(), tf.device('/cpu:0'):

    # Input data.
    train_dataset = tf.placeholder(tf.int32, shape=[batch_size])
    train_labels = tf.placeholder(tf.int32, shape=[batch_size, 1])

    # Variables.
    embeddings = tf.Variable(
      tf.random_uniform([vocabulary_size, embedding_size], -1.0, 1.0))
    softmax_weights = tf.Variable(
      tf.truncated_normal([vocabulary_size, embedding_size],
                           stddev=1.0 / math.sqrt(embedding_size)))
    softmax_biases = tf.Variable(tf.zeros([vocabulary_size]))

    # Model.
    # Look up embeddings for inputs.
    embed = tf.nn.embedding_lookup(embeddings, train_dataset)
    # Compute the softmax loss, using a sample of the negative labels each time.
    logits = tf.nn.bias_add(tf.matmul(embed,tf.transpose(softmax_weights)),softmax_biases)
    labels = tf.one_hot(train_labels,vocabulary_size)
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits = logits))

    # Optimizer.
    # Note: The optimizer will optimize the softmax_weights AND the embeddings.
    # This is because the embeddings are defined as a variable quantity and the
    # optimizer's `minimize` method will by default modify all variable quantities 
    # that contribute to the tensor it is passed.
    # See docs on `tf.train.Optimizer.minimize()` for more details.
    optimizer = tf.train.AdagradOptimizer(1.0).minimize(loss)
    
    norm = tf.sqrt(tf.reduce_sum(tf.square(embeddings), 1, keep_dims=True))
    normalized_embeddings = embeddings / norm

  num_steps = 10000

  with tf.Session(graph=graph) as session:
    tf.global_variables_initializer().run()
    print('Initialized')
    average_loss = 0
    for step in range(num_steps):
      batch_data, batch_labels = generate_batch(batch_size,data)
      feed_dict = {train_dataset : batch_data, train_labels : batch_labels}
      _, l = session.run([optimizer, loss], feed_dict=feed_dict)
      average_loss += l
      if step % 2000 == 0:
        if step > 0:
          average_loss = average_loss / 2000
        # The average loss is an estimate of the loss over the last 2000 batches.
        print('Average loss at step %d: %f' % (step, average_loss))
        average_loss = 0
    final_embeddings = normalized_embeddings.eval()

  tsne = TSNE(perplexity=30, n_components=2, init='pca', n_iter=5000, method='exact')
  two_d_embeddings = tsne.fit_transform(final_embeddings)
  
  with open('../data/allembed.pkl','wb') as f:
    pickle.dump(final_embeddings.tolist(),f)
  with open('../data/2dembed.pkl','wb') as f:
    pickle.dump(two_d_embeddings.tolist(),f)

locate_entities()