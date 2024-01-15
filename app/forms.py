from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import URLField
from wtforms.validators import DataRequired


class NewLinkForm(FlaskForm):
    url = URLField('URL', validators=[DataRequired()])


class DeleteLinkForm(FlaskForm):
    link_id = HiddenField()
