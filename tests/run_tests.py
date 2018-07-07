from elasticsearch import Elasticsearch,RequestsHttpConnection,helpers
import time
from empty_index import empty_index
from test_read import test_read
from test_write import test_write

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
test_dir = '/home/lpang/Documents/GitHub/news-visualizer-local-test/aws/'
prod_dir = '/home/lpang/Documents/GitHub/news-visualizer/aws/'

while True:
    #reload automatically
    input_str = input().split(' ')
    test,query = input_str[0],' '.join(input_str[1:])
    t1 = time.time()
    result = None
    if test=='0':
        result = empty_index(es)
    elif test=='1':
        result = test_read(es,query)
    elif test=='2':
        result = test_write(es)
    t2 = time.time()
    print(result)
    print('time elapsed: '+str(t2-t1)+' seconds')
    with open(test_dir+'read.py') as f1:
        with open(prod_dir+'read-lambda/read.py','w') as f2:
            f2.write(f1.read())
            print('wrote to read.py')
    with open(test_dir+'write.py') as f1:
        with open(prod_dir+'write-lambda/write.py','w') as f2:
            f2.write(f1.read())
            print('wrote to write.py')
