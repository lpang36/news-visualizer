import pickle
import json

def output_json(target):
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
    
  edges = {}
  with open('../data/edges.pkl','rb') as f:
    edges = pickle.load(f)
  
  data = {}
  data['nodes'] = []
  data['edges'] = []
  for name in kws_table:
    data['nodes'].append({
      'id': name,
      'label': name,
      'x': embed[kws_table[name]][0],
      'y': embed[kws_table[name]][1],
      'size': kws[kws_table[name]][0]
    })
  for i,edge in enumerate(edges):
    data['edges'].append({
      'id': 'e'+str(i),
      'source': kws[edge[0]][1],
      'target': kws[edge[1]][1],
      'value': edges[edge]
    })
    
  with open('../data/graph.json','wb') as f:
    json.dump(data,f)
  
output_json('donald trump')