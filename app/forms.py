from flask_wtf import FlaskForm
from wtforms import URLField
from wtforms.validators import DataRequired, URL


class NewBookmarkForm(FlaskForm):
    url = URLField('URL', validators=[DataRequired()])
