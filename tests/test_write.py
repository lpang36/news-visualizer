def test_write(es):
    import write
    from s3_interface import load_from_s3 as s3_load,save_to_s3 as s3_save
    return write.write(None,None,es,s3_load,s3_save)
