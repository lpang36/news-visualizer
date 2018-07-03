import json
from elasticsearch import Elasticsearch,RequestsHttpConnection,helpers

BONSAI_URL = 'https://ezq74z6t3a:gc0wwgwdvp@news-visualizer-2976423464.us-east-1.bonsaisearch.net'
ITEMS_PER_DOC = 4

def connectES(esEndPoint):
  print ('Connecting to the ES Endpoint {0}'.format(esEndPoint))
  try:
    esClient = Elasticsearch(
    hosts=[{'host': esEndPoint, 'port': 443}],
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection)
    return esClient
  except Exception as E:
    print("Unable to connect to {0}".format(esEndPoint))
    print(E)
    exit(3)
es = connectES(BONSAI_URL)

def read(event,context):  
  event['q'] = event['q'].lower()
  should_match  = []
  for i in range(ITEMS_PER_DOC):
    for j in ['description','title']:
      should_match.append({
        'match': {
            j+'_'+str(i): {
              'query':event['q'],
              '_name':str(i)
            }
        }
      })
  query = {
    'query': {
      'bool': {
        'should': should_match
      }
    }
  }
  articles = es.search(index='news-visualizer',doc_type='article',body=query,size=10000)['hits']['hits']
  
  def process_article(article,ind):
    return {'title':article['title_'+str(ind)],'time':article['time_'+str(ind)],'url':article['url_'+str(ind)]}
  
  ### compute edges ###
  edges = {}
  nodes = {}
  #sentiments = {}
  for a in articles:
    matched = [int(num) for num in a['matched_queries']]
    a = a['_source']
    for ind in range(ITEMS_PER_DOC):
      if ind in matched:
        temp = sorted(ast.literal_eval(a['keywords_'+str(ind)]))
        for i in range(len(temp)):
          for j in range(i+1,len(temp)):
            if (temp[i],temp[j]) in edges:
              edges[(temp[i],temp[j])]+=1
              #sentiments[(temp[i],temp[j])]+=articles[inds[k]]['sentiment']
            else:
              edges[(temp[i],temp[j])] = 1
              #sentiments[(temp[i],temp[j])] = articles[inds[k]]['sentiment']
          if temp[i] in nodes:
            nodes[temp[i]]['size']+=1
            nodes[temp[i]]['articles'].append(process_article(a))
          else:
            nodes[temp[i]] = {'id':temp[i],'label':temp[i],'size':1,'articles':[process_article(a,ind)]}
  
  ### output json ###
  output = {} #beware of duplicate name
  output['nodes'] = [nodes[n] for n in nodes]
  output['edges'] = []
  for i,edge in enumerate(edges):
    output['edges'].append({
      'id': 'e'+str(i),
      'source': edge[0],
      'target': edge[1],
      'value': edges[edge]
    })
    
  #with open('./temp/graph.json','wb') as f:
  #  json.dump(output,f)
  
  return {
    'isBase64Encoded': True,
      'statusCode': 200,
      'body': json.dumps(output),
      'headers': {
         'Content-Type': 'application/json', 
         'Access-Control-Allow-Origin': '*' 
     }
  }

#read({'q':'trump'},None)