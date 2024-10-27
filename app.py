from flask import Flask, render_template, request, jsonify
from PIL import Image
import os
import shutil

app = Flask(__name__)
UPLOAD_FOLDER = 'static/images'
SORTED_FOLDER = 'static/sorted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure sorted folders are created
for i in range(1, 4):
    os.makedirs(os.path.join(SORTED_FOLDER, f'Folder{i}'), exist_ok=True)

def slice_image(image_path, slice_width, slice_height):
    img = Image.open(image_path)
    img_width, img_height = img.size
    slices = []
    slice_count = 1  # Start naming from 1

    # Generate slices and name them sequentially
    for y in range(0, img_height, slice_height):
        for x in range(0, img_width, slice_width):
            box = (x, y, min(x + slice_width, img_width), min(y + slice_height, img_height))
            slice_img = img.crop(box)
            slice_path = os.path.join(UPLOAD_FOLDER, f'{slice_count}.png')
            slice_img.save(slice_path)
            slices.append(f'{slice_count}.png')
            slice_count += 1

    return slices

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        slice_width = int(request.form.get('slice_width', 60))
        slice_height = int(request.form.get('slice_height', 40))
        
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            slices = slice_image(filepath, slice_width, slice_height)
            return render_template('index.html', big_image=file.filename, slices=slices)
    return render_template('index.html')

@app.route('/sort_image', methods=['POST'])
def sort_image():
    data = request.json
    image_name = data.get('image')
    folder_number = data.get('folder')
    
    if not image_name or not folder_number:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Define the destination folder path
    dest_folder = os.path.join(SORTED_FOLDER, f'Folder{folder_number}')
    dest_path = os.path.join(dest_folder, image_name)
    
    # Initialize source_path as None
    source_path = None
    
    # Debugging: Print the name of the image and folder being processed
    print(f"Processing image: {image_name}, Target Folder: Folder{folder_number}")
    
    # Check if the image exists in the upload folder
    upload_path = os.path.join(UPLOAD_FOLDER, image_name)
    if os.path.exists(upload_path):
        source_path = upload_path
        print(f"Image found in UPLOAD_FOLDER: {upload_path}")
    else:
        # Check each sorted folder to see if the image exists there
        for folder in os.listdir(SORTED_FOLDER):
            current_folder_path = os.path.join(SORTED_FOLDER, folder)
            current_image_path = os.path.join(current_folder_path, image_name)
            
            if os.path.exists(current_image_path):
                source_path = current_image_path
                print(f"Image found in sorted folder: {current_image_path}")
                break
    
    # If source_path is still None, the image was not found in any location
    if not source_path:
        print("Image not found in any source location.")
        return jsonify({'error': 'Image not found in source location'}), 404

    # Move the image to the new destination folder
    try:
        shutil.move(source_path, dest_path)
        print(f"Image moved to: {dest_path}")

        # Renaming all files in the destination folder to follow a sequential naming convention
        images = sorted(os.listdir(dest_folder))
        for i, filename in enumerate(images, start=1):
            old_path = os.path.join(dest_folder, filename)
            new_path = os.path.join(dest_folder, f"{i}.png")
            os.rename(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")

        return jsonify({'message': f'Image moved and renamed in Folder {folder_number}'}), 200
    except Exception as e:
        print(f"Error during moving/renaming: {e}")
        return jsonify({'error': 'An error occurred while sorting the image'}), 500

if __name__ == '__main__':
    app.run(debug=True)
