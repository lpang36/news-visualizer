import imp
test_dir = '/home/lpang/Documents/GitHub/news-visualizer-local-test/aws/'
module = imp.load_source('write',test_dir+'write.py')

def test_read(es):
    module = imp.reload(module)
    return module.write(None,None,es)
