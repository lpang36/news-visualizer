import sys
import requests
import os.path
import pickle
import re
from copy import copy

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
      blacklist.append(line.replace('\n',''))
  
  terms = {a[1]:a[0] for a in filter(lambda x: x[0]>=10,[(terms[i],i) for i in terms])}
  temp = copy(terms)
  
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
          merge(temp,t,t[:-i])
          break
  terms = temp
  temp = copy(terms)
  
  #check blacklist
  for t in terms:
    if t in blacklist:
      del temp[t]
  terms = temp
  temp = copy(terms)
      
  #check names
  terms = sorted([(terms[i],i) for i in terms],reverse=True)
  for _,t in terms:
    if len(t.split(' '))==1:
      for _,s in terms:
        if t!=s and len(s)>len(t) and s.rfind(t)==len(s)-len(t):
          merge(temp,t,s)
          break
  terms = temp
  temp = copy(terms)
  
  #check exception list
  for t in terms:
    for i,e in enumerate(exceptions):
      if t in e:
        merge(temp,t,targets[i])
        break
  terms = temp
        
  kws = sorted([(terms[i],i) for i in terms],reverse=True)
  with open('../data/keywords.pkl','wb') as f:
    pickle.dump(kws,f)

compile_keywords()