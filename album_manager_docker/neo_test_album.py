import socket
from logging.handlers import RotatingFileHandler
from time import strftime
import logging as log
import threading
from BaseHTTPServer import HTTPServer
from prometheus_client import Summary, MetricsHandler, Counter, generate_latest
import flask
from flask import request, jsonify, send_from_directory, Response
import os
import logging
import traceback

app = flask.Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
folder_name='app-data/images'
app.config['UPLOAD_FOLDER'] = folder_name
PROMETHEUS_PORT = 9000
CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
trace_log_path='app-data/trace.log'

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'DESC: Time spent processing request')
INDEX_TIME = Summary('index_request_processing_seconds', 'DESC: INDEX time spent processing request')

# Create a metric to cound the number of runs on process_request()
c = Counter('requests_for_host', 'Number of runs of the process_request method', ['method', 'endpoint'])

def counter():
    path = str(request.path)
    verb = request.method
    label_dict = {"method": verb,
                 "endpoint": path}
    c.labels(**label_dict).inc()

# A route to Upload images to album.
@app.route('/api/v1/resources/upload', methods=['GET','POST'])
@INDEX_TIME.time()
def home():
    try:
        counter()
        if request.method == 'POST':
            images_target = os.path.join(APP_ROOT, '{}'.format(folder_name))
            if not request.form['album_Name']:
                message = [{"Exit Code": "500", "Content": "Album name not given"}]
                return jsonify(message)
            album_Name = request.form['album_Name']
            target = os.path.join(images_target + '/' + album_Name)
            print(target)
            if not os.path.isdir(images_target):
                os.mkdir(images_target)
            if not os.path.isdir(target):
                os.mkdir(target)
            print(request.files.getlist("file"))
            for upload in request.files.getlist("file"):
                print(upload)
                if not upload.filename:
                    message = [{"Exit Code": "500", "Content": "Image name not given"}]
                    return jsonify(message)
                print("{} is the file name".format(upload.filename))
                filename = upload.filename
                # This is to verify files are supported
                ext = os.path.splitext(filename)[1]
                if (ext == ".jpg") or (ext == ".png"):
                    print("File supported moving on...")
                else:
                    message = [{"Exit Code": "500", "Content": "File not supported"}]
                    return jsonify(message)
                destination = "/".join([target, filename])
                print("Accept incoming file:", filename)
                print("Save it to:", destination)
                upload.save(destination)
            message = [{"Exit Code": "200", "Content": "Image file upload successful"}]
            return jsonify(message)
    except Exception as e:
        print str(e)
        message = [{"Exit Code": "500", "Content": "Image file upload failed"}]
        return jsonify(message)
    return """
        <!doctype html>
        <title>Upload Image File</title>
        <h1>Upload Image File</h1>
        <form action="" method=post enctype=multipart/form-data>
            <input type="text" name="album_Name"><br>
            <input type=file name=file>
             <input type=submit value=Upload>
        </form>
        
        """

# A route to return all of the available albums & images.
@app.route('/api/v1/resources/listalbum/all', methods=['GET'])
@INDEX_TIME.time()
def list_all():
    try:
        counter()
        album_image_list=[]
        album_names = os.listdir(folder_name)
        for album_name in album_names:
            album_imagelist = {}
            album_imagelist["albumName"]=album_name
            print album_imagelist
            images = ",".join(os.listdir(folder_name + "/" + album_name))
            album_imagelist["Images"] = images
            print album_imagelist
            album_image_list.append(album_imagelist)
        return jsonify(album_image_list)
    except Exception as e:
        print str(e)
        message=[{"Exit Code": "500","Content":"Album Name not given"}]
        return jsonify(message)

# A route to return all of the available images from given album.
@app.route('/api/v1/resources/listalbum', methods=['GET'])
@INDEX_TIME.time()
def list_album():
    counter()
    if 'albumName' in request.args:
        album=request.args['albumName']
        album_image_list = []
        album_names = os.listdir(folder_name)
        for album_name in album_names:
            album_imagelist = {}
            album_imagelist["albumName"] = album_name
            images = ",".join(os.listdir(folder_name + "/" + album_name))
            album_imagelist["Images"] = images
            album_image_list.append(album_imagelist)
        print album_image_list
        results=[]
        for album_image in album_image_list:
            if album_image['albumName']==album:
                results.append(album_image)
        print results
        if results:
            return jsonify(results)
        else:
            message = [{"Exit Code": "500", "Content": 'Album '+request.args['albumName']+' is not present'}]
            return jsonify(message)
    else:
        message = [{"Exit Code": "500", "Content": "Album Name not given"}]
        return jsonify(message)

# A route to delete given images in given album.
@app.route('/api/v1/resources/delete', methods=['GET','POST'])
@INDEX_TIME.time()
def delete():
    counter()
    if 'imageName' in request.args:
        albumName,image=request.args['imageName'].split(':')
        if not os.path.isdir(os.path.join(APP_ROOT, '{}/{}'.format(folder_name,albumName))):
            message = [{"Exit Code": "500", "Content": "Album is not present"}]
            return jsonify(message)
        if not os.path.exists(os.path.join(APP_ROOT, '{}/{}/{}'.format(folder_name,albumName,image))):
            message = [{"Exit Code": "500", "Content": "Image is not present"}]
            return jsonify(message)
        os.remove(os.path.join(APP_ROOT, '{}/{}/{}'.format(folder_name,albumName,image)))
        print 'deleted '+image+' from album '+albumName
        message = [{"Exit Code": "200", "Content": "Image deleted successfully"}]
        return jsonify(message)
    else:
        message = [{"Exit Code": "500", "Content": "Image Name not given"}]
        return jsonify(message)

# A route to view given images in given album.
@app.route('/api/v1/resources/view')
@INDEX_TIME.time()
def send_image():
    print request.method
    counter()
    if 'imageName' in request.args:
        albumName, image = request.args['imageName'].split(':')
        if not os.path.isdir(os.path.join(APP_ROOT, '{}/{}'.format(folder_name,albumName))):
            message = [{"Exit Code": "500", "Content": "Album is not present"}]
            return jsonify(message)
        if not os.path.exists(os.path.join(APP_ROOT, '{}/{}/{}'.format(folder_name,albumName,image))):
            message = [{"Exit Code": "500", "Content": "Image is not present"}]
            return jsonify(message)
        return send_from_directory("images", os.path.join('{}/{}'.format(albumName,image)))
    else:
        message = [{"Exit Code": "500", "Content": "Image file not given"}]
        return jsonify(message)

# A route to display events/requests handled.
@app.route('/api/v1/resources/events')
@INDEX_TIME.time()
def events():
    counter()
    f = open(trace_log_path)
    f_read=f.read()
    f.close()
    return Response(f_read, mimetype='text/plain')

@app.after_request
def after_request(response):
    """ Logging after every request. """
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if 'view' in request.full_path:
        response_data='Displaying image'
        print response_data
    if 'events' not in request.full_path and 'view' not in request.full_path:
        response_data = response.get_data()
    if 'events' in request.full_path:
        response_data='Displaying events'
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.error('\n%s \n %s %s %s %s %s \n%s',
                      ts,
                      request.remote_addr,
                      request.method,
                      request.scheme,
                      request.full_path,
                      response.status, response_data)
    return response

@app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)
    return "Internal Server Error", 500

@app.route('/metrics')
def metrics():
    return Response(generate_latest(),mimetype=CONTENT_TYPE_LATEST)

# Seperate web server for prometheus scraping
class PrometheusEndpointServer(threading.Thread):
    """A thread class that holds an http and makes it serve_forever()."""
    def __init__(self, httpd, *args, **kwargs):
        self.httpd = httpd
        super(PrometheusEndpointServer, self).__init__(*args, **kwargs)

    def run(self):
        self.httpd.serve_forever()

# keep the server running
def start_prometheus_server():
    try:
        httpd = HTTPServer(("0.0.0.0", PROMETHEUS_PORT), MetricsHandler)
    except (OSError, socket.error):
        return

    thread = PrometheusEndpointServer(httpd)
    thread.daemon = True
    thread.start()
    log.info("Exporting Prometheus /metrics/ on port %s", PROMETHEUS_PORT)

start_prometheus_server()

if __name__ == "__main__":
    # maxBytes to small number, in order to demonstrate the generation of multiple log files (backupCount).
    handler = RotatingFileHandler(trace_log_path, maxBytes=10000, backupCount=3)
    # getLogger(__name__):   decorators loggers to file + werkzeug loggers to stdout
    # getLogger('werkzeug'): decorators loggers to file + nothing to stdout
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    app.run(debug=True, host='0.0.0.0',port=5001)