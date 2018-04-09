import sys
import requests
import os.path
import pickle
import re

import nltk
from nltk.tag import pos_tag, StanfordNERTagger
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordTokenizer
      
def compile_keywords():
  tags = []
  with open('../data/tags.pkl','rb') as f:
    tags = pickle.load(f)
  
  def update(D,K):
    if K in D:
      D[K]+=1
    else:
      D[K] = 1

  terms = {}
  regex = re.compile(r'/[A-Z]+')
  for tag in tags:
    for i in tag.subtrees(filter=lambda x: x.label()=='NE'):
      update(terms,regex.sub('',str(i.flatten())[4:-1]).lower())
    #add nnp leaves
    
  exceptions = []
  targets = []
  blacklist = []
  with open('../data/exceptions.txt','r') as f:
    for line in f:
      temp = []
      for i in line.split(','):
        temp.append(i.replace('\n',''))
      exceptions.append(temp)
  with open('../data/targets.txt','r') as f:
    for line in f:
      targets.append(line.replace('\n',''))
  with open('../data/blacklist.txt','r') as f:
    for line in f:
      blacklist.append(line)
  
  terms = {a[1]:a[0] for a in filter(lambda x: x[0]>=5,[(terms[i],i) for i in terms])}
  
  def merge(D,K,T):
    if T in D:
      D[T]+=D[K]
    else:
      D[T] = D[K]
    del D[K]
  
  #check common endings
  for t in terms:
    if len(t)>4 and (t[-1]=='n' or t[-1]=='s'):
      for i in range(1,4):
        if t[:-i] in terms:
          merge(terms,t,t[:-i])
          break
  
  #check blacklist
  for t in terms:
    if t in blacklist:
      del terms[t]
      
  #check names
  for t in terms:
    for 
  
  #check exception list
  for t in terms:
    for i,e in enumerate(exceptions):
      if t in e:
        merge(terms,t,targets[i])
        break
        
  print [x[1] for x in sorted(filter(lambda x: x[0]>=5,[(terms[i],i) for i in terms]),reverse=True)]

compile_keywords()