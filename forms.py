from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, validators
from wtforms.validators import DataRequired, Email, Length, NumberRange


class RegistrationForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[
                        DataRequired(), Email(), Length(max=50)])
    password = PasswordField('Contraseña', validators=[
                             DataRequired(), Length(min=6, max=50)])
    website = StringField('Sitio Web', validators=[
                          DataRequired(), Length(max=50)])
    hostDB = StringField('Host DB', validators=[
                         DataRequired(), Length(max=100)])
    userDB = StringField('Usuario DB', validators=[
                         DataRequired(), Length(max=100)])
    passwordDB = PasswordField('Contraseña DB', validators=[Length(max=100)])
    databaseDB = StringField('Nombre de la BD', validators=[
                             DataRequired(), Length(max=50)])

    # Selección del tipo de base de datos
    db_type = SelectField('Tipo de DB', choices=[
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('sqlserver', 'SQL Server'),
        ('sqlite', 'SQLite'),
        ('oracle', 'Oracle')
    ], validators=[DataRequired()])

    port = IntegerField('Puerto', [
        validators.Optional(),
        validators.NumberRange(
            min=1, max=65535, message="El puerto debe estar entre 1 y 65535")
    ])
    ssl_enabled = SelectField(
        'SSL habilitado',
        choices=[('true', 'Sí'), ('false', 'No')],
        default='false',
        validators=[DataRequired()]
    )
    charset = StringField('Charset', validators=[Length(max=50)])
    submit = SubmitField('Registrar')
