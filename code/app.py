from flask import Flask, render_template, request,send_file
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'images'
app.config['OUTPUT_FOLDER']= 'output'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
            content_image = request.files['input-image']
            style_image = request.files['style-image']
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg')):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'))
            content_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg'))
            style_image.save(os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg'))
            import train
            return render_template('index.html',output_image=True)
    else:
            return render_template('index.html')

@app.route('/20.jpg')
def output_image():
    return send_file('output/20.jpg', mimetype='image/jpg')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8501, debug=True)