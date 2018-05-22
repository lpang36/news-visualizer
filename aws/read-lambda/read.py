def read(event,context):  
  import json
  from s3_interface import load_from,save_to
  
  articles = load_from('articles.txt')
  
  def process_article(article):
    return {'title':article['title'],'time':article['time'],'url':article['url']}
  
  ### compute edges ###
  edges = {}
  nodes = {}
  event['q'] = event['q'].lower()
  #sentiments = {}
  for a in articles:
    if event['q'] in a['title'].lower() or event['q'] in a['description'].lower(): #needs refining
      temp = sorted(a['keywords'])
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
          nodes[temp[i]] = {'id':temp[i],'label':temp[i],'size':1,'articles':[process_article(a)]}
  
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
    
  with open('./temp/graph.json','wb') as f:
    json.dump(output,f)
  
  return output

read({'q':'trump'},None)