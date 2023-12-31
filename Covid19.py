# -*- coding: utf-8 -*-

import tensorflow as tf
import numpy as np
from flask import Flask, render_template, request, flash, redirect, url_for, make_response
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import os

labels = []
for line in tf.gfile.GFile('output_labels.txt').readlines():
    labels.append(line.strip())

def create_graph():
    graph = tf.Graph()
    graph_def = tf.GraphDef()
    with open('output_graph.pb', 'rb') as f:
        graph_def.ParseFromString(f.read())
    with graph.as_default():
        tf.import_graph_def(graph_def)
    return graph

def read_image(path, height=299, width=299, mean=128, std=128):
    file_reader = tf.read_file(path, 'file_reader')
    if path.endswith('.png'):
        image_reader = tf.image.decode_png(file_reader, channels=3, name='png_reader')
    elif path.endswith('.gif'):
        image_reader = tf.squeeze(tf.image.decode_gif(file_reader, name='gif_reader'))
    elif path.endswith('.bmp'):
        image_reader = tf.image.decode_bmp(file_reader, name='bmp_reader')
    else:
        image_reader = tf.image.decode_jpeg(file_reader, channels=3, name='jpeg_reader')
    image_np = tf.cast(image_reader, tf.float32)
    image_np = tf.expand_dims(image_np, 0)
    image_np = tf.image.resize_bilinear(image_np, [height, width])
    image_np = tf.divide(tf.subtract(image_np, [mean]), [std])
    sess = tf.Session()
    image_data = sess.run(image_np)
    return image_data

def classify_image(image, top_k=1):
    image_data = read_image(image)

    graph = create_graph()

    with tf.Session(graph=graph) as sess:
        input_operation = sess.graph.get_operation_by_name('import/Mul')
        output_operation = sess.graph.get_operation_by_name('import/final_result')
        predictions = sess.run(output_operation.outputs[0], feed_dict={input_operation.outputs[0]: image_data})
        predictions = np.squeeze(predictions)

        top_k = predictions.argsort()[-top_k:]
        for i in top_k:
            return labels[i]

app = Flask(__name__,static_url_path='') 
bootstrap = Bootstrap(app) 
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/', methods=['POST', 'GET'])
def process():
    if request.method == 'POST':
        f = request.files.get('selectfile') 
        if f:
            basepath = os.path.dirname(__file__)  
            filename = secure_filename(f.filename)
            uploadpath = os.path.join(basepath, 'static/uploads', secure_filename(filename))
            f.save(uploadpath)  

            pred = classify_image(uploadpath)
            flash('Upload Load Successful!', 'success')  
            return render_template('base.html', imagename=filename, predvalue=pred)
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)


