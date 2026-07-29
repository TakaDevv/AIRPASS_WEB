from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, IntegerField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class RegisterForm(FlaskForm):
    fullname = StringField("Nom complet", validators=[DataRequired(), Length(min=3, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField("Telephone", validators=[Optional(), Length(max=30)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirmer le mot de passe",
                             validators=[DataRequired(), EqualTo("password", message="Les mots de passe ne correspondent pas.")])


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])


class ProfileForm(FlaskForm):
    fullname = StringField("Nom complet", validators=[DataRequired(), Length(min=3, max=150)])
    phone = StringField("Telephone", validators=[Optional(), Length(max=30)])
    password = PasswordField("Nouveau mot de passe (laisser vide pour ne pas changer)",
                              validators=[Optional(), Length(min=6)])


class StadiumForm(FlaskForm):
    name = StringField("Nom du stade", validators=[DataRequired(), Length(max=150)])
    city = StringField("Ville", validators=[DataRequired(), Length(max=100)])
    capacity = IntegerField("Capacite", validators=[DataRequired(), NumberRange(min=1)])


class EventForm(FlaskForm):
    title = StringField("Titre de l'evenement", validators=[DataRequired(), Length(max=200)])
    stadium_id = SelectField("Stade", coerce=int, validators=[DataRequired()])
    date = StringField("Date (AAAA-MM-JJ HH:MM)", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional()])
    base_price = FloatField("Prix de base (DA)", validators=[DataRequired(), NumberRange(min=0)])


class SeatForm(FlaskForm):
    section = StringField("Section", validators=[DataRequired(), Length(max=20)])
    row = StringField("Rangee", validators=[DataRequired(), Length(max=10)])
    number = IntegerField("Numero", validators=[DataRequired(), NumberRange(min=1)])
    price = FloatField("Prix (DA)", validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField("Statut", choices=[("disponible", "Disponible"), ("reserve", "Reserve")])
