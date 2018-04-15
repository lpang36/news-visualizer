import sys
import requests
import os.path
import pickle
import re
from copy import copy
import random
import math
import numpy
from matplotlib import pylab, colors

def compute_edges(target):
  kws = []
  with open('../data/keywords.pkl','rb') as f:
    kws = pickle.load(f)
  kws_table = {}
  for i,t in enumerate(kws):
    for w in t[1:]:
      kws_table[w] = i 
  
  embed = []
  with open('../data/2dembed.pkl','rb') as f:
    embed = pickle.load(f)
  if target in kws_table:
    embed[kws_table[target]] = [sum([a for a,_ in embed])/len(embed),sum([a for _,a in embed])/len(embed)]
  
  data = []
  with open('../data/entitydata.pkl','rb') as f:
    data = pickle.load(f)
    
  edges = {}
  for row in data:
    temp = sorted(row)
    for i in range(len(temp)):
      for j in range(i+1,len(temp)):
        if (temp[i],temp[j]) in edges:
          edges[(temp[i],temp[j])]+=1
        else:
          edges[(temp[i],temp[j])] = 1
  
  def plot(embeddings, labels, edges, keywords):
    assert len(embeddings) >= len(labels), 'More labels than embeddings'
    pylab.figure(figsize=(15,15))	# in inches
    for i, label in enumerate(labels):
      x, y = embeddings[i]
      pylab.scatter(x, y, s=keywords[i][0], c='blue')
      pylab.annotate(label, xy=(x, y), xytext=(5, 2), textcoords='offset points',
                     ha='right', va='bottom')
    limit = max(edges.values())+0.0
    for i in edges:
      pylab.plot([embeddings[i[0]][0],embeddings[i[1]][0]],[embeddings[i[0]][1],embeddings[i[1]][1]],lw=math.log(edges[i]+1),c=(1,0,0,edges[i]/limit))
    pylab.show()

  plot(embed, [a[1] for a in kws], edges, kws)
  
compute_edges("donald trump")