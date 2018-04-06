import sys
import requests
import os.path
import pickle
import re

import nltk
from nltk.tag import pos_tag, StanfordNERTagger
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordTokenizer

recompute_articles = False
articles = []

if os.path.exists('../data/articles.pkl') and not recompute_articles:
  with open('../data/articles.pkl','rb') as f:
    articles = pickle.load(f)
else:
  key = ''
  with open('key.txt',"r") as file:
    key = file.read().replace('\n','')

  for i in range(1,2):
    url = 'https://newsapi.org/v2/everything?q=trump&language=en&sortBy=publishedAt&apiKey='+key+'&pageSize=100&page='+str(i)
    r = requests.get(url)
    for article in r.json()[u'articles']:
      if article[u'title'] is None:
        article[u'title'] = ''
      if article[u'description'] is None:
        article[u'description'] = ''
      if article[u'publishedAt'] is None:
        article[u'publishedAt'] = ''
      articles.append((article[u'title'].encode('ascii','ignore'),article[u'description'].encode('ascii','ignore'),article[u'publishedAt'].encode('ascii','ignore')))
  
  print articles
  with open('../data/articles.pkl','wb') as f:
    pickle.dump(articles,f)
    
# First, the punkt tokenizer divides our text in sentences.
# Each sentence is then tokenized and POS tagged.
#
# Proper nouns receive the tags 'NPP', we discard first words of sentence to
# reduce the false positive rate. For example, in the following sentence,
# onomatopoeias are tagged as NPP: "Bang! Ssssssss! It exploded.".

#st = StanfordNERTagger('english.all.3class.distsim.crf.ser.gz') 

def proper_noun_tag(sentence):
  #return st.tag(sentence.split())
  sent = nltk.pos_tag(nltk.word_tokenize(sentence))
  return nltk.ne_chunk(sent,binary=True)

recompute_tags = False
tags = []

if os.path.exists('../data/tags.pkl') and not recompute_tags:
  with open('../data/tags.pkl','rb') as f:
    tags = pickle.load(f)
else:
  sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
  for title,description,_ in articles:
    tags.append(proper_noun_tag(title))
    for sentence in sent_detector.tokenize(description):
        tags.append(proper_noun_tag(sentence))
        
  with open('../data/tags.pkl','wb') as f:
    pickle.dump(tags,f)
      
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
  for i in tag.subtrees(filter=lambda x: x.label()=='NNP'):
    print i
    #update(terms
  