from flask import Flask, render_template, request, redirect, flash
# from flaskext.mysql import MySQL
import flask_login
from flask_login import login_required
from user import User
import pandas as pd
import dash
from view import LAYOUT, PROJECTDESK, USERCABINET
from view_specials import DATABASE, ADMINPAGE
from view_analysis import GRAPHIC, GANTT
from view_calendar import CALENDAR
from dash.dependencies import Input, Output, State
from sqlalchemy import text
import db
from os import makedirs
from callback import CACHE
import callback
from app import appDash, app, login_manager, engine, cache


@login_manager.user_loader
def loadUser(user_id):
    user=db.get_user_info(user_id)
    if user is None: return
    USER = User()
    USER.id = user[0]
    USER.username = user[1]
    USER.relevant = user[2]
    USER.admin = user[3]
    USER.name = user[4]
    USER.color = user[5]
    USER.passord = user[6]
    return USER

@app.route('/')
@login_required
def main():
    user = flask_login.current_user.name
    return redirect('/dash/')

@app.route('/loginpage')
def loginpage():
    return render_template('index.html')
@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/loginpage')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if password == '' or username == '':
        flash('Не все поля были заполнены!')
        return redirect('/loginpage')
    row = db.get_user(username)
    if row is None:
        flash('Такого пользователя нет!')
        return redirect('/loginpage')
    psswd = row[1]
    if password != psswd:
        flash('Неверный пароль! Попробуйте снова')
        return redirect('/loginpage')
    id = row[0]
    user = loadUser(user_id=id)
    flask_login.login_user(user, remember=True)
    return redirect('/')

@app.login_manager.unauthorized_handler
def unathor():
    return redirect('/loginpage')

#------------DASH---------------
appDash.layout = LAYOUT('Анна Бурлака','','1, 1, 1, 0')
appDash.title = 'LPTV'
@app.before_request
def restrict_dash():
    if request.path.startswith('/dash') and not flask_login.current_user.is_authenticated:
        return redirect('/loginpage')

@appDash.callback(
    Output('content', 'children'),
    Input('prjBtn', 'n_clicks'),
    Input('calBtn', 'n_clicks'),
    Input('graphBtn', 'n_clicks'),
    Input('ganttBtn', 'n_clicks'),
    Input('dbBtn', 'n_clicks'),
    Input('admBtn', 'n_clicks'),
    Input('cabinetBtn', 'n_clicks'),
    Input('calAction', 'n_clicks',  allow_optional=True),
    Input('graphAction', 'n_clicks',  allow_optional=True),
    State('selected-project-id', 'data', allow_optional=True)
)
def display_page(prjBtn, calBtn, graphBtn,ganttBtn, dbBtn, admBtn,cabinetBtn, calAction, graphAction, project_id):
    triggered = dash.callback_context.triggered
    CACHE.clear()
    if not triggered:
        return PROJECTDESK()

    changed_id = triggered[0]['prop_id'].split('.')[0]
    if not project_id:
        project_id = db.get_user_last_project(flask_login.current_user.id)

    match changed_id:
        case 'prjBtn':
            return PROJECTDESK()
        case 'calBtn' | 'calAction':
            return CALENDAR(project_id)
        case 'graphBtn':
            return GRAPHIC()
        case 'ganttBtn':
            return GANTT()
        case 'graphAction':
            return GRAPHIC(project_id, True)
        case 'dbBtn':
            return DATABASE()
        case 'admBtn':
            return ADMINPAGE()
        case 'cabinetBtn':
            return USERCABINET()
        case _:
            return PROJECTDESK()


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=8080, debug=True)
