import requests
import re
import json
from copy import copy
from nltk import pos_tag,ne_chunk,word_tokenize
from nltk.data import load

def generate_graph(event,context):
  ### extract keywords ###
  key = ''
  with open('./data/key.txt',"r") as file:
    key = file.read().replace('\n','')
      
  articles = []
  for i in range(1,26):
    url = 'https://newsapi.org/v2/everything?q='+event['q']+'&language=en&sortBy=publishedAt&apiKey='+key+'&pageSize=100&page='+str(i)
    r = requests.get(url)
    for article in r.json()[u'articles']:
      if article[u'title'] is None:
        article[u'title'] = ''
      if article[u'description'] is None:
        article[u'description'] = ''
      if article[u'publishedAt'] is None:
        article[u'publishedAt'] = ''
      articles.append((article[u'title'].encode('ascii','ignore'),article[u'description'].encode('ascii','ignore'),article[u'publishedAt'].encode('ascii','ignore')))

  # First, the punkt tokenizer divides our text in sentences.
  # Each sentence is then tokenized and POS tagged.
  #
  # Proper nouns receive the tags 'NPP', we discard first words of sentence to
  # reduce the false positive rate. For example, in the following sentence,
  # onomatopoeias are tagged as NPP: "Bang! Ssssssss! It exploded.".

  #st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 
  def proper_noun_tag(sentence):
    #return st.tag(sentence.split())
    sent = pos_tag(word_tokenize(sentence))
    return ne_chunk(sent,binary=True)

  recompute_tags = False
  tags = []

  sent_detector = load('file:./data/english.pickle')
  for title,description,_ in articles:
    tags.append(proper_noun_tag(title))
    for sentence in sent_detector.tokenize(description):
      tags.append(proper_noun_tag(sentence))
  
  ### compile keywords ###
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
  with open('./data/exceptions.txt','r') as f:
    for line in f:
      temp = []
      for i in line.split(','):
        temp.append(i.replace('\n',''))
      exceptions.append(temp)
  with open('./data/targets.txt','r') as f:
    for line in f:
      targets.append(line.replace('\n',''))
  with open('./data/blacklist.txt','r') as f:
    for line in f:
      blacklist.append(line.replace('\n',''))
  
  terms = {a[1]:a[0] for a in filter(lambda x: x[0]>=10,[(terms[i],i) for i in terms])}
  temp = copy(terms)
  aliases = {a:[] for a in terms}
  
  def merge(D,K,T,A):
    if T in D:
      D[T]+=D[K]
      A[T].extend(A[K])
    else:
      D[T] = D[K]
      A[T] = copy(A[K])
    del D[K]
    del A[K]
  
  #check common endings
  for t in terms:
    if len(t)>4 and (t[-1]=='n' or t[-1]=='s'):
      for i in range(1,4):
        if t[:-i] in terms:
          merge(temp,t,t[:-i],aliases)
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
          merge(temp,t,s,aliases)
          break
  terms = temp
  temp = copy(terms)
  
  #check exception list
  for t in terms:
    for i,e in enumerate(exceptions):
      if t in e:
        merge(temp,t,targets[i],aliases)
        break
  terms = temp
        
  kws = sorted([[terms[i],i]+aliases[i] for i in terms],reverse=True)
  
  ### locate entities ###
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
  
  ### compute edges ###
  edges = {}
  for row in data:
    temp = sorted(row)
    for i in range(len(temp)):
      for j in range(i+1,len(temp)):
        if (temp[i],temp[j]) in edges:
          edges[(temp[i],temp[j])]+=1
        else:
          edges[(temp[i],temp[j])] = 1
  
  ### output json ###
  data = {} #beware of duplicate name
  data['nodes'] = []
  data['edges'] = []
  for name in kws_table:
    data['nodes'].append({
      'id': name,
      'label': name,
      'size': kws[kws_table[name]][0]
    })
  for i,edge in enumerate(edges):
    data['edges'].append({
      'id': 'e'+str(i),
      'source': kws[edge[0]][1],
      'target': kws[edge[1]][1],
      'value': edges[edge]
    })
    
  with open('./temp/graph.json','wb') as f:
    json.dump(data,f)
    
generate_graph({'q':'trump'},None)