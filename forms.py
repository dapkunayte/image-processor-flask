from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets import ColorInput


class TextToImageForm(FlaskForm):
    text = StringField('text', validators=[DataRequired()])
    text_color = StringField('text_color', validators=[DataRequired()], widget=ColorInput())
    background_color = StringField('background_color', validators=[DataRequired()], widget=ColorInput())
    text_size = IntegerField('text_size', validators=[DataRequired(), NumberRange(min=4, max=72)])
    image_size = SelectField('image_size', choices=["320x200", "800x600", "1024x768", "1080x1080", "1280x1024",
                                                    "1600x900"])
    position = SelectField(u'category', choices=["вверху слева", "по центру", "слева", "вверху по центру",
                                                 "вверху справа", "внизу справа", "внизу слева",
                                                 "справа", "внизу по центру"])
    submit = SubmitField('Получить изображение')
