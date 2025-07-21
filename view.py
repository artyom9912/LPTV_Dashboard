import datetime
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import flask_login
from dash import dash_table
from datetime import date
import plotly.graph_objects as go
import pandas as pd
import db
from utils import get_user_picture, rgba_string_to_hex


filterItems = [
    "Актуальные",
    "Архивные",
    "Все"
]

def LAYOUT(username, role, color):
    print(role)
    layout = html.Div([dcc.Location(id='url', refresh=False),
                       dbc.Row([
                           html.Div([
                               html.A(html.Button([
                                   html.Span([], className='ico7', id='miniBtnSpan'), '',
                               ], className='sm'), id='miniBtn', n_clicks=0),
                               html.Div([
                                   html.Img(src=get_user_picture(db.get_user_login(username)), className='userPic', id='UserPic'),
                                   html.Div(username, className='userName', id='USER'),
                                   html.Div(role, className='userRole', id='ROLE'),
                               ], className='userBox'),
                               html.Div([
                                   html.A(html.Button([
                                       html.Span([], className='ico1'), 'Доска проектов',
                                   ], className='button option'), id='prjBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico2'), 'Календарь',
                                   ], className='button option'), id='calBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico3'), 'База данных',
                                   ], className='button option'), id='dbBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico5'), 'График',
                                   ], className='button option'), id='graphBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico9'), 'Диаграмма Ганта',
                                   ], className='button option'), id='ganttBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico6'), 'Личный кабинет',
                                   ], className='button option'), id='cabinetBtn', n_clicks=0),
                                   html.A(html.Button([
                                       html.Span([], className='ico4'), 'Администрация',
                                   ], className='button option'), id='admBtn', n_clicks=0)
                               ], className='options')
                           ], className='side menu', id='menu'),
                           html.Div([
                               html.Div([
                                   html.Div([
                                       html.Div(className='logo', style=dict(width=50, height=50), id='LOGO'),
                                       html.Div([
                                           html.Div(['LPTV DESIGN'], className='title'),
                                           html.Div(['dashboard & management'], className='subtitle')
                                       ], className='titleBox'),
                                   ], className='banner'),
                                   html.Div([
                                       html.A(
                                           html.Button([
                                               html.Span([], className='icon1'), 'Обновить'
                                           ], className='button'), href='/dash/'),
                                       html.A(html.Button([
                                           html.Span([], className='icon2'), 'Выйти',
                                       ], className='button exit'), href='/logout')
                                   ], className='buttons')
                               ], className='header'),
                               # -------------CONTENT-------------#
                               html.Div([],
                                        className='content', id='content')
                           ], className='side main', id='main')
                       ])
                       ])
    return layout


def PROJECTDESK():
    Years = db.get_years()
    today = datetime.datetime.now()
    rel = db.get_project_count()
    irrel = db.get_project_count(0)
    content = html.Div(
        [
            dcc.Store(id='selected-project-id', data=None),
            html.Div('ДОСКА ПРОЕКТОВ', className='name'),
            html.Div([
                html.Div([irrel, html.Span('завершено', className='tail')], className='cloud number line'),
                html.Div([rel, html.Span('актуальных', className='tail')], className='cloud number line'),
            ], className='line-wrap'),
            html.Div([
                html.Div([
                    html.Div([], className='grid', id='ProjectDesk'),
                ], className='cloud desk line'),
                html.Div([
                    html.Div([
                        html.Div('Фильтры', className='silence', ),
                        dcc.Dropdown(id='RelevantFilterDesk', placeholder='', style=dict(width=170, marginTop=15), clearable=False,
                                     options=[{'label': i, 'value': i} for i in filterItems], value='Актуальные'),
                        dcc.Dropdown(id='YearFilterDesk', placeholder='Год', style=dict(width=170, marginTop=15, marginBottom=25),
                                     options=[{'label': i, 'value': i} for i in Years], value=str(today.year)),
                    ], className='cloud filter'),

                    html.Div([
                        html.Div('Действия', className='silence', ),
                        html.Div(html.Button([
                            html.Span([], className='ico2'), '',
                        ], className='button action'), id='calAction', n_clicks=0, className='action-wrap'),
                        html.Div(html.Button([
                            html.Span([], className='ico5'), '',
                        ], className='button action'), id='graphAction', n_clicks=0, className='action-wrap'),
                    ], className='cloud filter hidden', id='ProjectInfo',
                        style={'margin-top': '20px', 'user-select': 'none',})
                ], className='filter line'),
            ], className='line-wrap focus'),
        ], style=dict(height='100%'))
    return content

def USERCABINET():
    user_data = flask_login.current_user
    user_color = rgba_string_to_hex(user_data.color)
    Years = db.get_years()
    today = datetime.datetime.now()
    rel = db.get_project_count_by_user(1, user_data.id)
    irrel = db.get_project_count_by_user(0, user_data.id)

    content = html.Div(
        [
            dcc.Store(id='selected-project-id', data=None),
            html.Div('ЛИЧНЫЙ КАБИНЕТ', className='name'),
            html.Div([
                html.Div([], id='popupCab', className='line')
            ], id='popupBoxCab', className='line'),
            html.Div([
                html.Div([irrel, html.Span('завершеных проектов', className='tail')], className='cloud number line'),
                html.Div([rel, html.Span('актуальных проектов', className='tail')], className='cloud number line'),
            ], className='line-wrap'),

            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            # Заголовок
                            html.Div(
                                [
                                    user_data.name.upper(),
                                    html.Span(
                                        'id: '+str(user_data.id),
                                        style=dict(fontFamily='"Noah Regular", monospace', marginLeft=8, fontSize=14,),
                                        className='silence'
                                    )
                                ],
                                id='ModalHead',
                                style={
                                    'background-color': user_color,
                                    'padding': '12px',
                                    'borderRadius': '6px'
                                }
                            ),

                            # Основное тело
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Имя", style={'margin-bottom': 0, 'color': '#999'}),
                                        dcc.Input(id='UserNameCab', placeholder='Имя сотрудника', className='inp',
                                                  value=user_data.name),

                                        dbc.Label("Логин", style={'margin-bottom': 0, 'color': '#999'}),
                                        dcc.Input(id='UserLoginCab', placeholder='Логин', className='inp',
                                                  value=user_data.username),

                                        dbc.Label("Пароль", style={'margin-bottom': 0, 'color': '#999'}),
                                        dcc.Input(id='UserPassCab', placeholder='Пароль', className='inp',
                                                  value=user_data.password),
                                    ], width=6),

                                    dbc.Col([
                                        dbc.Label("Фото", style={'margin-bottom': 0, 'color': '#999'}),
                                        html.Div(id='UploadBlock')
                                    ], width=6)
                                ], className="gx-5"),

                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Роль"),
                                        html.Div(['Администратор' if user_data.admin else 'Дизайнер'], className='cloud')
                                    ], width=6),

                                    dbc.Col([
                                        dbc.Label("Цвет"),
                                        dbc.Input(
                                            type="color",
                                            id="UserColorCab",
                                            value=user_color,
                                            className='colorpicker'
                                        )
                                    ], width=6)
                                ], className="gx-5"),

                            ], style={'paddingLeft': 16, 'paddingTop': 16, 'paddingBottom': 16}),

                            # Кнопки
                            html.Div([
                                dbc.Button(
                                    "Обновить фото",
                                    id="ChangePic",
                                    n_clicks=0,
                                    className="button cloud submit",
                                    style={'marginLeft': '12px'}
                                ),
                                dbc.Button(
                                    "Сохранить",
                                    n_clicks=0,
                                    id="CabinetSubmit",
                                    className="button cloud submit",
                                    style={'marginLeft': '12px'}
                                )
                            ], style={'textAlign': 'right', 'marginTop': '16px'})
                        ], id='DialogContent',
                            style={ 'padding': '22px 0 0 0'}
                        )
                    ])
                ], className='cloud line'),

            ], className='line-wrap focus'),
        ], style=dict(height='100%')
    )

    return content
