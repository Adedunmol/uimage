import imghdr
import os
from flask import current_app, abort
import secrets


#This function checks the stream data passed in and returns the format of the image data
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')



def save_image(data):
    uploaded_file = data
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext == '.jpeg':
            file_ext = '.jpg'
        f_name = secrets.token_hex(8)
        if file_ext != validate_image(uploaded_file.stream):
            abort(400)
        new_filename = f_name + file_ext
        uploaded_file.save(os.path.join(os.path.dirname(__file__), current_app.config['UPLOAD_PATH'], new_filename))
    return new_filename