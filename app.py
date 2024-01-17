import os
from rembg import remove
from PIL import Image #Python Imaging Library 
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory
import mysql.connector
# from PIL import ImageFilter

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'webp'])

if 'static' not in os.listdir('.'):
    os.mkdir('static')

if 'uploads' not in os.listdir('static/'):
    os.mkdir('static/uploads')

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 4
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret key"

# Define your MySQL database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thamarai5118',
    'database': 'bg_re'
}

# Create a MySQL database connection
db = mysql.connector.connect(**db_config)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def remove_background(input_path, output_path):
    input = Image.open(input_path)
    output = remove(input)
    output = output.convert("RGBA")  # Ensure the image format is RGBA
    output.save(output_path, "PNG")  # Save the processed image in PNG format

@app.route('/')
def home():
    return render_template('home.html')

# Add a new route for photo enhancement
@app.route('/enhance', methods=['POST'])
def enhance():
    file = request.files['file']
    if file and allowed_file(file.filename):
        # Delete existing files in UPLOAD_FOLDER
        delete_existing_files(app.config['UPLOAD_FOLDER'])

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Load the uploaded image
        input_path = UPLOAD_FOLDER + '/' + filename
        input_image = Image.open(input_path)

        # Perform image enhancement (e.g., increase brightness)
        enhancer = ImageEnhance.Brightness(input_image)
        enhanced_image = enhancer.enhance(1.5)  # You can adjust the enhancement factor as needed

        # Save the enhanced image
        enhanced_img_name = filename.split('.')[0] + "_enhanced.png"
        output_path = UPLOAD_FOLDER + '/' + enhanced_img_name
        enhanced_image.save(output_path)

        download_link = f"/download/{enhanced_img_name}"  # Generate the download link

        return render_template('home.html', org_img_name=filename, enhanced_img_name=enhanced_img_name, download_link=download_link)


@app.route('/remback', methods=['POST'])
def remback():
    file = request.files['file']
    if file and allowed_file(file.filename):
        # Delete existing files in UPLOAD_FOLDER
        delete_existing_files(app.config['UPLOAD_FOLDER'])

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        rembg_img_name = filename.split('.')[0] + "_rembg.png"
        input_path = UPLOAD_FOLDER + '/' + filename
        output_path = UPLOAD_FOLDER + '/' + rembg_img_name
        remove_background(input_path, output_path)

        # Store the image data in the MySQL database
        with open(output_path, 'rb') as image_file:
            image_data = image_file.read()

        current_timestamp = datetime.now()  # Get the current timestamp

        cursor = db.cursor()
        insert_query = "INSERT INTO images (original_name, rembg_name, image_data, timestamp) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (filename, rembg_img_name, image_data, current_timestamp))
        db.commit()
        cursor.close()

        download_link = f"/download/{rembg_img_name}"  # Generate the download link

        return render_template('home.html', org_img_name=filename, rembg_img_name=rembg_img_name, download_link=download_link)


# @app.route('/rotate', methods=['POST'])
# def rotate():
#     file = request.files['file']
#     if file and allowed_file(file.filename):
#         # Delete existing files in UPLOAD_FOLDER
#         delete_existing_files(app.config['UPLOAD_FOLDER'])

#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

#         input_path = UPLOAD_FOLDER + '/' + filename
#         input_image = Image.open(input_path)

#         # Perform image rotation
#         rotated_image = input_image.rotate(45)  # You can adjust the rotation angle

#         # Save the rotated image
#         rotated_img_name = filename.split('.')[0] + "_rotated.png"
#         output_path = UPLOAD_FOLDER + '/' + rotated_img_name
#         rotated_image.save(output_path)

#         download_link = f"/download/{rotated_img_name}"  # Generate the download link

#         return render_template('home.html', org_img_name=filename, rotated_img_name=rotated_img_name, download_link=download_link)
    
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


def delete_existing_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            
if __name__ == '__main__':
    app.run(debug=True)
