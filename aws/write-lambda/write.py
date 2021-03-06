import requests
import re
import json
import os
import time
import datetime
from copy import deepcopy
#import nltk
from nltk import pos_tag,ne_chunk,word_tokenize
from nltk.data import load
from nltk.corpus import words
#from textblob import TextBlob as tb
from elasticsearch import Elasticsearch,RequestsHttpConnection,helpers
from ast import literal_eval
try:
  from s3_interface import load_from_s3 as load_from,save_to_s3 as save_to
except:
  load_from = None
  save_to = None

BONSAI_URL = 'https://ezq74z6t3a:gc0wwgwdvp@news-visualizer-2976423464.us-east-1.bonsaisearch.net'
ITEMS_PER_DOC = 4

def connectES(esEndPoint):
  print ('Connecting to the ES Endpoint {0}'.format(esEndPoint))
  try:
    esClient = Elasticsearch(BONSAI_URL)
    return esClient
  except Exception as E:
    print("Unable to connect to {0}".format(esEndPoint))
    print(E)
    exit(3)
es = connectES(BONSAI_URL)

def write(event,context,es=es,load_from=load_from,save_to=save_to):
  #if 'LAMBDA_TASK_ROOT' in os.environ:
  #  nltk.data.path.append(os.environ['LAMBDA_TASK_ROOT']+'nltk_data')

  ### extract keywords ###
  key = ''
  with open('./data/key.txt',"r") as file:
    key = file.read().replace('\n','')
      
  articles = []
  sources = 'metro,mirror,reddit-r-all,bbc-news,cnn,fox-news,al-jazeera-english,msnbc,nbc-news,news24,the-globe-and-mail,the-guardian-uk,the-new-york-times,the-huffington-post,the-telegraph,the-wall-street-journal,usa-today,vice-news,wired,abc-news,associated-press,cbc-news'
  last_time = datetime.datetime.fromtimestamp(time.time()-4*60*60).isoformat()
  limit = 100000
  i = 1
  while i < limit/100:    
    url = 'https://newsapi.org/v2/everything?language=en&sortBy=publishedAt&from='+last_time+'&apiKey='+key+'&sources='+sources+'&pageSize=100&page='+str(i)
    r = requests.get(url)
    limit = r.json()[u'totalResults']
    for article in r.json()[u'articles']:
      if article[u'title'] is None:
        article[u'title'] = ''
      if article[u'description'] is None:
        article[u'description'] = ''
      if article[u'publishedAt'] is None:
        article[u'publishedAt'] = ''
      if article[u'url'] is None:
        article[u'url'] = ''
      #sum = 0
      #if article[u'title']!='' or article[u'description']!='':
      #  blob = tb(article[u'title']+'.'+article[u'description'])
      #  for s in blob.sentences:
      #    sum+=s.sentiment.polarity
      articles.append({'title':article[u'title'].encode('ascii','ignore'),'description':article[u'description'].encode('ascii','ignore'),'time':article[u'publishedAt'].encode('ascii','ignore'),'url':article[u'url'].encode('ascii','ignore')})
    #print 'page '+str(i)
    i+=1
    
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

  sent_detector = load('file:./nltk_data/tokenizers/punkt/english.pickle')
  for a in articles:
    title,description = a['title'],a['description']
    tags.append(proper_noun_tag(title))
    for sentence in sent_detector.tokenize(description):
      tags.append(proper_noun_tag(sentence))
  #print 'done sentence tagging'
  
  # terms: array of terms like ([default,term1,term2...],count)
  # term_to_ind: dictionary of terms like term: index
  # default_terms: array of default terms
  # temp: same as terms but with changes made
  def make_reverse(arr):
    output = {}
    for i,a in enumerate(arr):
      for term in a[0]:
        output[term] = i
    return output
  
  terms = load_from('terms.txt')
  term_to_ind = make_reverse(terms)
  new_terms = {}
  
  count = len(terms)
  regex = re.compile(r'/[A-Z]+')
  for tag in tags:
    for i in tag.subtrees(filter=lambda x: x.label()=='NE'):
      name = regex.sub('',str(i.flatten())[4:-1]).lower()
      if name in term_to_ind:
        terms[term_to_ind[name]][1]+=1
      elif name in new_terms:
        new_terms[name]+=1
      else:
        new_terms[name] = 1
  terms.extend([[name],new_terms[name]] for name in new_terms)
  #add nnp leaves
              
  #if len(terms)>100: #heuristic for eliminating terms
  terms = [v for v in terms if v[1]>1]      
  term_to_ind = make_reverse(terms)
    
  exceptions = []
  targets = []
  blacklist = []
  word_names = []
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
  with open('./data/words.txt','r') as f:
    for line in f:
      word_names.append(line.replace('\n',''))
  
  # D: array like terms
  # K: index
  # T: index
  # we always use the earlier index for backwards compatibility
  # syntax is merging K (source) into T (target)
  def merge(D,K,T):
    if not D[K] or not D[T] or K==T:
      return
    D[T][1]+=D[K][1]
    D[T][0].extend(D[K][0])
    D[K] = False
  
  temp = deepcopy(terms)
  #check common endings
  for t in term_to_ind:
    if len(t)>4 and (t[-1]=='n' or t[-1]=='s'):
      for i in range(1,4):
        if t[:-i] in term_to_ind:
          merge(temp,term_to_ind[t],term_to_ind[t[:-i]])
          break
  terms = [t for t in temp if t]
  temp = deepcopy(terms)
  term_to_ind = make_reverse(terms)
                                     
  #check blacklist
  for t in term_to_ind:
    if t in blacklist:
      temp[term_to_ind[t]] = False
  terms = [t for t in temp if t]          
      
  #check names (first and last)
  terms = sorted([(i[1],i[0]) for i in terms],reverse=True)
  terms = [[i[1],i[0]] for i in terms] #convert back to list
  temp = deepcopy(terms)
  for i,temp_list in enumerate(terms):
    t_list = temp_list[0]
    for t in t_list:
      if len(t.split(' '))==1:
        flag = False
        for j in range(len(terms)):
          for s in terms[j][0]:
            if i!=j and t!=s and len(s.split(' '))==2 and s.split(' ')[1]==t:
              merge(temp,i,j)
              flag = True
              break
            #removing first names for now...
            elif i!=j and t!=s and len(s.split(' '))==2 and s.split(' ')[0]==t:
              merge(temp,i,j)
              flag = True
              break
          if flag:
            break
        if flag:
          break
  terms = [t for t in temp if t]
  temp = deepcopy(terms)
  term_to_ind = make_reverse(terms)
  
  #check exception list
  added_terms = {} #bug fix
  for t in term_to_ind:
    for i,e in enumerate(exceptions):
      if t in e:
        target = 0
        if targets[i] not in term_to_ind and targets[i] not in added_terms:
          temp.append([[targets[i]],0])
          added_terms[targets[i]] = len(temp)-1
          target = len(temp)-1
        elif targets[i] not in term_to_ind:
          target = added_terms[targets[i]]
        else:
          target = term_to_ind[targets[i]]
        merge(temp,term_to_ind[t],target)
        break
  terms = [t for t in temp if t]
  temp = deepcopy(terms)
  term_to_ind = make_reverse(terms)

  #check common words
  for t in term_to_ind:
    if len(t)<5 and t not in word_names and t in words.words():
      temp[term_to_ind[t]] = False
  terms = [t for t in temp if t]
  term_to_ind = make_reverse(terms)  
  
  for i,a in enumerate(articles):
    title,description = a['title'],a['description']
    temp = (title+description).lower()
    row = set()
    for k in term_to_ind:
      if ' '+k in temp or k+' ' in temp:
        row.add(terms[term_to_ind[k]][0][0])
    a['keywords'] = list(row)
    
  #index new articles to elasticsearch
  new_articles = []
  for i in range(0,len(articles),4):
    docs = {}
    for j in range(ITEMS_PER_DOC):
      for key in articles[i+j]:
        docs[key+'_'+str(j)] = str(articles[i+j][key])
    docs['doc_time'] = str(articles[i]['time'])
    docs['_index'] = 'news-visualizer'
    docs['_type'] = 'doc'
    docs['_op_type'] = 'index'
    new_articles.append(docs)
  helpers.bulk(es,new_articles)
  
  #delete old articles
  week_ago = datetime.datetime.strftime(datetime.datetime.fromtimestamp(time.time()-7*24*60*60),'%Y-%m-%dT%H:%M:%SZ')
  delete_query = {
    'query': {
      'range': {
        'doc_time': {
          'lt':week_ago
        }
      }
    }
  }
  es.delete_by_query(index='news-visualizer',doc_type='article',body=delete_query,size=10000)
  
  #update keywords
  needs_updating = {}
  for i,_ in terms:
    for term in i[1:]:
      needs_updating[term] = i[0]
  
  existing_articles = es.search(index='news-visualizer',doc_type='doc',body={'query':{'match_all':{}}},size=10000)['hits']['hits']
  ctr = 0
  updated_articles = []
  for a in existing_articles:
    article = a['_source']
    for j in range(ITEMS_PER_DOC):
      if 'keywords_'+str(j) in article:
        keywords = literal_eval(article['keywords_'+str(j)])
        for i in range(len(keywords)-1,-1,-1):
          kw = keywords[i]
          if kw in needs_updating:
            keywords[i] = needs_updating[kw]
          if kw not in term_to_ind:
            del keywords[i]
        article['keywords_'+str(j)] = str(keywords)
    updated_articles.append(article)
  
  for i,a in enumerate(updated_articles):
    a['_index'] = 'news-visualizer'
    a['_type'] = 'doc'
    a['_op_type'] = 'update'
    updated_articles[i] = a
  helpers.bulk(es,updated_articles)
  
  save_to(str(terms),'terms.txt')
  
  return {
    'isBase64Encoded': True,
      'statusCode': 200,
      'body': '',
      'headers': {
         'Content-Type': 'application/json', 
         'Access-Control-Allow-Origin': '*' 
     }
  }
  
#write({'q':'trump'},None)
