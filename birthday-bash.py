from flask import Flask, render_template, request
from werkzeug import secure_filename
import random
import string
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def upload_file():
   return render_template('upload.html')

@app.route('/uploadajax', methods = ['GET', 'POST'])
def upload_file1():
   if request.method == 'POST':
      f = request.files['file']
      extention = "."+(f.filename.split('.')[-1])
      f.filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))+extention
      print f.filename
      filename = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
      return 'file uploaded successfully'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)