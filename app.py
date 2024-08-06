from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os

import face_recognition
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image
import shutil

app = Flask(__name__)
CORS(app)  # Enable CORS
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/kycupload', methods=['POST'])
def upload_file():
    if 'adhar' not in request.files or 'image' not in request.files:
        print('No file part in request)
        return jsonify({'result': 'Error: No file part'}), 400

    adhar_file = request.files['adhar']
    image_file = request.files['image']

    if not (adhar_file and allowed_file(adhar_file.filename)):
        print('Invalid Aadhaar file')
        return jsonify({'result': 'Error: Invalid Aadhaar file'}), 400
    if not (image_file and allowed_file(image_file.filename)):
        print('Invalid image file')
        return jsonify({'result': 'Error: Invalid image file'}), 400

    adhar_filename = secure_filename(adhar_file.filename)
    image_filename = secure_filename(image_file.filename)

    adhar_path = os.path.join(app.config['UPLOAD_FOLDER'], 'adhar.' + adhar_filename.rsplit('.', 1)[-1])
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'image.' + image_filename.rsplit('.', 1)[-1])

    adhar_file.save(adhar_path)
    image_file.save(image_path)

    print(f'Saved Aadhaar file to: {adhar_path}')
    print(f'Saved image file to: {image_path}')

    try:
        result = perform_kyc(adhar_path, image_path)
        print(f'KYC Result: {result}')
    finally:
        cleanup_upload_folder()

    return jsonify({'result': result})

def perform_kyc(adhar_path, image_path):
    # Convert Aadhaar PDF to image if needed
    if adhar_path.endswith('.pdf'):
        adhar_images = convert_from_path(adhar_path)
        adhar_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'adhar_image.jpg')
        adhar_images[0].save(adhar_image_path, 'JPEG')
    else:
        adhar_image_path = adhar_path

    try:
        # Load and convert Aadhaar image to RGB
        adhar_image = Image.open(adhar_image_path)
        if adhar_image.mode != 'RGB':
            adhar_image = adhar_image.convert('RGB')
        adhar_image.save(adhar_image_path)  # Save the converted image
        adhar_image = face_recognition.load_image_file(adhar_image_path)

        # Load and convert input image to RGB
        input_image = Image.open(image_path)
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        input_image.save(image_path)  # Save the converted image
        input_image = face_recognition.load_image_file(image_path)

        # Extract face encodings
        adhar_face_encodings = face_recognition.face_encodings(adhar_image)
        input_face_encodings = face_recognition.face_encodings(input_image)

        # Log face encoding counts
        print(f'Number of faces found in Aadhaar image: {len(adhar_face_encodings)}')
        print(f'Number of faces found in input image: {len(input_face_encodings)}')

        # Check if faces are detected in both images
        if not adhar_face_encodings:
            return 'KYC Unsuccessful: No face found in Aadhaar image.'
        if not input_face_encodings:
            return 'KYC Unsuccessful: No face found in input image.'

        # Compare faces
        adhar_face_encoding = adhar_face_encodings[0]
        input_face_encoding = input_face_encodings[0]

        matches = face_recognition.compare_faces([adhar_face_encoding], input_face_encoding)
        print(f'Face match result: {matches}')

        if matches[0]:
            return 'KYC Successful'
        else:
            return 'KYC Unsuccessful'
    except Exception as e:
        print(f'Exception occurred: {str(e)}')
        return f'KYC Unsuccessful: {str(e)}'

def cleanup_upload_folder():
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except Exception as e:
        print(f'Error cleaning up upload folder: {str(e)}')

