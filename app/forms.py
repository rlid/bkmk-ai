from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import URLField
from wtforms.validators import DataRequired


class NewBookmarkForm(FlaskForm):
    url = URLField('URL', validators=[DataRequired()])


class DeleteBookmarkForm(FlaskForm):
    bookmark_id = HiddenField()


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')
