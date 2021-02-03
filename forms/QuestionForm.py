from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Required, Email

class QuestionForm(FlaskForm):
    """Question form."""

    products = [
        ('learn-ultra', 'Blackboard Learn Ultra'), 
        ('learn-original', 'Blackboard Learn Original'), 
        ('bb-data', 'Blackboard Data'), 
        ('bb-ally', 'Blackboard Ally'), 
        ('bb-collab', 'Blackboard Collaborate'), 
        ('bb-analytics', 'Blackboard Analytics'), 
        ('bb-classroom', 'Blackboard Classroom'), 
        ('bb-mobile', 'Blackboard Mobile Apps'), 
        ('bb-wcm', 'Blackboard Web Community Manager'), 
        ('bb-mass', 'Blackboard Mass Communications'), 
        ('bb-connect', 'Blackboard Connect'), 
        ('bb-other', 'Other')
    ]

    
    gname = StringField('Given Name', [
        DataRequired()])
    fname = StringField('Family Name', [
        DataRequired()])
    email = StringField('Email', [
        Email(message=('Not a valid email address.')),
        DataRequired()])
    institution = StringField('Institution', [
        DataRequired()])
    product = SelectField('Product', choices=products )
    question = TextAreaField('Question', [
        DataRequired(),
        Length(min=4, message=('Your message is too short.'))])
    submit = SubmitField('Submit')