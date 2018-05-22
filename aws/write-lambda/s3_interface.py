import ast

def load_from(filename):
  with open(filename,'r') as file:
    return ast.literal_eval(file.read())

def save_to(data,filename):
  with open(filename,'w') as file:
    file.write(str(data))