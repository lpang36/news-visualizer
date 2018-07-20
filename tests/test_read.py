def test_read(es,query):
    import read
    return read.read({'q':query},None,es)
