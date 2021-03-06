
import ast
import boto3
import botocore

def load_from_local(filename):
  with open(filename,'r') as file:
    return ast.literal_eval(file.read())

def save_to_local(data,filename):
  with open(filename,'w') as file:
    file.write(str(data))

def load_from_s3(filename):
  s3 = boto3.resource('s3')
  BUCKET_NAME = 'news-visualizer-bucket' 
  KEY = filename
  obj = s3.Object(BUCKET_NAME,KEY)
  return ast.literal_eval(obj.get()['Body'].read().decode('utf-8'))
  
def save_to_s3(data,filename):
  s3 = boto3.resource('s3')
  BUCKET_NAME = 'news-visualizer-bucket' 
  KEY = filename
  obj = s3.Object(BUCKET_NAME,KEY)
  obj.put(Body=data)
