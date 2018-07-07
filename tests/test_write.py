import imp
test_dir = '/home/lpang/Documents/GitHub/news-visualizer-local-test/aws/'
module = imp.load_source('write',test_dir+'write.py')
s3_load = imp.load_source('load_from_s3',test_dir+'s3_interface.py')
s3_save = imp.load_source('save_to_s3',test_dir+'s3_interface.py')

def test_write(es):
    module = imp.reload(module)
    return module.write(None,None,es,s3_load,s3_save)
