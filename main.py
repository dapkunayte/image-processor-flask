import os
from flask import Flask, request, redirect, flash, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from rembg.bg import remove
from forms import TextToImageForm
import io

UPLOAD_FOLDER = 'imgs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'a really really really really long secret key'


def allowed_file(filename):
    """ Функция проверки расширения файла """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def black_and_white_dithering(input_image_path, output_image_path, dithering=True):
    color_image = Image.open(input_image_path)
    if dithering:
        bw = color_image.convert('1')
    else:
        bw = color_image.convert('1', dither=Image.NONE)
    bw.save(output_image_path)


def text_to_image_draw(output_image_path, input_text, background_color, text_color, text_size, image_size, position):
    width, height = tuple(int(x) for x in image_size.split("x"))
    im = Image.new('RGB', (width, height), color=background_color)
    font = ImageFont.truetype("times.ttf", size=int(text_size))
    draw = ImageDraw.Draw(im)
    text_width, text_height = draw.textsize(input_text)
    if position == "вверху слева":
        text_position = (0, 0)
    elif position == "по центру":
        text_position = ((width-text_width)/2, (height-text_height)/2)
    elif position == "слева":
        text_position = (0, (height - text_height) / 2)
    elif position == "вверху по центру":
        text_position = ((width - text_width) / 2, 0)
    elif position == "вверху справа":
        text_position = ((width - text_width), 0)
    elif position == "внизу справа":
        text_position = ((width - text_width), (height - text_height))
    elif position == "внизу слева":
        text_position = (0, (height - text_height))
    elif position == "справа":
        text_position = ((width-text_width), (height-text_height)/2)
    elif position == "внизу по центру":
        text_position = (width-text_width)/2, (height-text_height)
    draw.text(text_position, input_text, fill=text_color, font=font)
    im.save(output_image_path)


def watermark_photo(input_image_path, output_image_path, watermark_image_path, position):
    base_image = Image.open(input_image_path)
    watermark = Image.open(watermark_image_path)
    width, height = base_image.size
    # add watermark to your image
    transparent = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    transparent.paste(base_image, (0, 0))
    transparent.paste(watermark, position, mask=watermark)
    transparent.save(output_image_path)


def remove_background(input_image_path, output_image_path):
    base_image = Image.open(input_image_path)
    base_image.save(input_image_path)
    bg_image = remove(base_image)
    bg_image.save(output_image_path)


def to_png(input_filename):
    output_filename = input_filename.replace(".jpeg", ".png")
    output_filename = input_filename.replace(".jpg", ".png")
    return output_filename


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/black_and_white', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # проверим, передается ли в запросе файл
        if 'file' not in request.files:
            # После перенаправления на страницу загрузки
            # покажем сообщение пользователю
            flash('Не могу прочитать файл')
            return redirect(request.url)
        file = request.files['file']
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # безопасно извлекаем оригинальное имя файла
            filename = secure_filename(file.filename)
            bw_filename = "bw_"+to_png(filename)
            # сохраняем файл
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            black_and_white_dithering('imgs/'+filename, 'imgs/'+bw_filename)
            # если все прошло успешно, то перенаправляем
            # на функцию-представление `download_file`
            # для скачивания файла
            return redirect(url_for('download_file', name=bw_filename))
        elif not(allowed_file(file.filename)):
            flash('Некорректное расширение файла. Доступны: .png, .jpeg, .jpg')
            return redirect(request.url)
    return render_template('upload.html')


@app.route('/text_to_image', methods=['GET', 'POST'])
def txt_to_img():
    form = TextToImageForm()
    if request.method == "POST":
        text_data = request.form['text']
        background_color = request.form['background_color']
        text_color = request.form['text_color']
        text_size = request.form['text_size']
        image_size = request.form['image_size']
        position = request.form['position']
        filename = "image.png"
        text_to_image_draw('imgs/'+filename, text_data, background_color, text_color, text_size, image_size, position)
        return redirect(url_for('download_file', name=filename))
    return render_template('text_to_image.html', form=form)


@app.route('/img_watermark', methods=['GET', 'POST'])
def add_img_watermark():
    if request.method == 'POST':
        if 'file1' not in request.files or 'file2' not in request.files:
                # После перенаправления на страницу загрузки
                # покажем сообщение пользователю
            flash('Не могу прочитать файл')
            return redirect(request.url)
        file1 = request.files['file1']
        file2 = request.files['file2']
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file1.filename == '' or file2.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            # безопасно извлекаем оригинальное имя файла
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
            wm_filename = "wm_"+to_png(filename1)
            watermark_photo('imgs/'+filename1, 'imgs/'+wm_filename, 'imgs/'+filename2, position=(0,0))
            return redirect(url_for('download_file', name=wm_filename))
        elif not(allowed_file(file1.filename)) or not(allowed_file(file2.filename)):
            flash('Некорректное расширение файла. Доступны: .png, .jpeg, .jpg')
            return redirect(request.url)
    return render_template('watermark.html')


@app.route('/remove_bg', methods=["GET", "POST"])
def remove_bg():
    if request.method == 'POST':
        # проверим, передается ли в запросе файл
        if 'file' not in request.files:
            # После перенаправления на страницу загрузки
            # покажем сообщение пользователю
            flash('Не могу прочитать файл')
            return redirect(request.url)
        file = request.files['file']
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # безопасно извлекаем оригинальное имя файла
            filename = secure_filename(file.filename)
            filename = filename.replace(".jpg",".png")
            bg_filename = "bg_" + to_png(filename)
            # сохраняем файл
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            remove_background('imgs/' + filename, 'imgs/' + bg_filename)
            # если все прошло успешно, то перенаправляем
            # на функцию-представление `download_file`
            # для скачивания файла
            return redirect(url_for('download_file', name=bg_filename))
        elif not (allowed_file(file.filename)):
            flash('Некорректное расширение файла. Доступны: .png, .jpeg, .jpg')
            return redirect(request.url)
    return render_template('background.html')


@app.route('/downloaded/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


if __name__ == '__main__':
    app.run(debug=True)
