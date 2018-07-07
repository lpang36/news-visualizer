from elasticsearch import Elasticsearch,RequestsHttpConnection,helpers

def empty_index(es):
    return es.delete_by_query(index='news-visualizer',doc_type='article',body={'query':{'match_all':{}}},size=10000)
