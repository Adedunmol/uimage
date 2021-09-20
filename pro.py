#!flask/bin/python
from werkzeug.middleware.profiler import ProfilerMiddleware
from image import app

app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(debug = True)