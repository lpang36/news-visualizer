import imp
test_dir = '/home/lpang/Documents/GitHub/news-visualizer-local-test/aws/'
module = imp.load_source('read',test_dir+'read.py')

def test_read(es,query):
    module = imp.reload(module)
    return module.read({'q':query},None,es)
