from flask import Flask, render_template, request, redirect, flash
# from flaskext.mysql import MySQL
import flask_login
from flask_login import login_required
from user import User
import pandas as pd
import dash
from view import LAYOUT, PROJECTDESK
from view_specials import DATABASE, ADMINPAGE
from view_analysis import GRAPHIC
from dash.dependencies import Input, Output
from sqlalchemy import text
import db
from os import makedirs
# from callback import update_db
import callback
from app import appDash, app, login_manager, engine, cache


@login_manager.user_loader
def loadUser(user_id):
    user=db.get_user_info(user_id)
    # print(user)
    if user is None: return
    USER = User()
    USER.id = user[0]
    USER.username = user[1]
    USER.relevant = user[2]
    USER.admin = user[3]
    USER.name = user[4]
    USER.color = user[5]
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
appDash.layout = LAYOUT('Артём Тюбаев','')
appDash.title = 'LPTV'
@app.route('/dash')
@flask_login.login_required
def projectDesk():
    appDash.layout = LAYOUT(flask_login.current_user.name, '')
    return appDash.run(debug=True)

# @cache.memoize()
# def getData():
#     con = engine.connect()
#     dbDF[0] = (pd.read_sql("""
#             SELECT YEAR(timestamp), MONTH(timestamp), DAY(timestamp), fullname, title, code, customer, hours
#             FROM skameyka.main_table
#             JOIN skameyka.project_table ON project_table.id = project_id
#             JOIN skameyka.user_table ON user_table.id = user_id
#             ORDER BY timestamp desc
#         """, con))
#     head = ['ГОД', 'ММ', 'ДД', 'СОТРУДНИК', 'ПРОЕКТ', 'ШИФР', 'ЗАКАЗЧИК', 'ЧАСЫ']
#     dbDF[0].columns = head


@appDash.callback(Output('content', 'children'),
              Input('prjBtn', 'n_clicks'),
              Input('calBtn', 'n_clicks'),
              Input('graphBtn', 'n_clicks'),
              Input('dbBtn', 'n_clicks'),
              Input('admBtn', 'n_clicks'))
def display_page(prjBtn, calBtn, graphBtn, dbBtn, admBtn):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # global dbDF
    # for i in range(0,len(calendar_cache)): del calendar_cache[0]



    if 'prjBtn' in changed_id:
        content = PROJECTDESK()
    # elif 'calBtn' in changed_id:
    #     content = CALENDAR()
    elif 'dbBtn' in changed_id:
        # JOIN для отображения бд
        # getData()
        # print(dbDF[0].shape)
        content = DATABASE()
    elif 'graphBtn' in changed_id:
        content = GRAPHIC(13)
    elif 'admBtn' in changed_id:
        content = ADMINPAGE()
    else:
        content = GRAPHIC(13)
    return content

if __name__ == '__main__':
    makedirs('cache-directory', exist_ok=True)
    app.run(host='127.0.0.1',port=8080, debug=True)
