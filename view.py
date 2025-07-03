import datetime
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash import dash_table
from datetime import date
import plotly.graph_objects as go
import pandas as pd
import db
from view_specials import DATABASE
from app import  engine

filterItems = [
    "Актуальные",
    "Архивные",
    "Все"
]


def GetDayName(name):
    if name == 'Monday':
        return 'ПН'
    elif name == 'Tuesday':
        return 'ВТ'
    elif name == 'Wednesday':
        return 'СР'
    elif name == 'Thursday':
        return 'ЧТ'
    elif name == 'Friday':
        return 'ПТ'
    elif name == 'Saturday':
        return 'СБ'
    elif name == 'Sunday':
        return 'ВС'


def LAYOUT(username, role):
    layout = html.Div([dcc.Location(id='url', refresh=False),
                       dbc.Row([
                           html.Div([
                               html.Div([
                                   html.Img(src='assets/img/artem.png', className='userPic'),
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
                                       html.Span([], className='ico4'), 'Администрация',
                                   ], className='button option'), id='admBtn', n_clicks=0)
                               ], className='options')
                           ], className='side menu'),
                           html.Div([
                               html.Div([
                                   html.Div([
                                       # html.Img(src='assets/img/logo.png', className='logo'),
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
                               # dcc.Loading([
                               html.Div([],
                                        className='content', id='content')
                               # ], color='grey', type='circle'),
                           ], className='side main')
                       ])
                       ])
    return layout


def PROJECTDESK():
    Years = db.get_years()
    Years.append("Всё время")

    rel = db.get_project_count()
    irrel = db.get_project_count(0)
    content = html.Div(
        [
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
                    html.Div('Фильтры', className='silence', ),
                    dcc.Dropdown(id='RelevantFilterDesk', placeholder='', style=dict(width=170, marginTop=15),
                                 options=[{'label': i, 'value': i} for i in filterItems], value='Актуальные'),
                    dcc.Dropdown(id='YearFilterDesk', placeholder='',  style=dict(width=170, marginTop=15),
                                 options=[{'label': i, 'value': i} for i in Years], value='Всё время'),
                ], className='cloud filter line'),
            ], className='line-wrap focus'), ], style=dict(height='100%'))
    return content

