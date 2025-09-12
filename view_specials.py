from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash import dash_table
from app import cache
import db


filterItems = [
    dbc.DropdownMenuItem("Актуальные"),
    dbc.DropdownMenuItem("Архивные"),
    dbc.DropdownMenuItem("Все"),
]

@cache.memoize()
def get_filters_cached():
    return db.get_filters()

def DATABASE():
    options = get_filters_cached()
    content = html.Div([
        html.Div('БАЗА ДАННЫХ', className='name'),
        html.Div([
            dcc.Loading([
            dash_table.DataTable(
                id='TableDB',
                fixed_rows={'headers': True,},
                page_current=0,
                page_size=40,
                page_action='custom',
                style_data={
                    'whiteSpace':'normal'
                },
                style_table={
                    'overflow': 'hidden',
                    'margin': '0',
                    'margin-top': '0px',
                    'padding': '0',
                    'width': '100%',
                    'height': 'fit-content',
                    'min-height':'400px',
                    'max-height':'100%',
                    'overflow-y':'auto',
                    'border': '0px solid white',
                    'borderRadius': '10px',
                    'transition':'all 0.12s ease-in-out',
                },
                style_cell={'font-family': 'Rubik', 'text-align': 'left', 'width':'auto',
                            'border': '2px solid white', 'background-color': '#f7f7f7',
                            'font-size': '14px', 'padding-left':'2px', 'cursor':'default'},
                style_header={'background-color': '#313131', 'color': 'white', 'height': '35px','z-index':'5',
                              'border': '0px solid white', 'font-family': 'Rubik', 'font-size': '14px',  'padding-left':'2px',},
                style_data_conditional=[
                    {
                        "if": {"state": "selected"},  # 'active' | 'selected'
                        "backgroundColor": "rgba(0, 116, 217, 0.3)",
                        'border': '2px solid white',
                    },
                ],
                style_cell_conditional=[
                                           {
                                               'if': {'column_id': 'hours'},
                                               'textAlign': 'center',
                                               'background-color': '#EAEAEA',
                                               'padding': '0',
                                               'width': '80px',
                                               'max-width': '80px',
                                           },
                                       ] + [
                                           {
                                               'if': {'column_id': col_id},
                                               # 'textAlign': 'center',
                                               'width':'70px',
                                               'padding': '0 8px'
                                           } for col_id in ('year', 'month', 'day')
                                       ]
            )], color='grey', type='circle'),
        ], className='db line'),
        html.Div([
        html.Div([
            html.Div('Группировка'.upper(), style={'margin-bottom': '10px','margin-top': '10px', 'font-weight':'700px', 'font-size':'18px','color':'black'}),
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(id='DayFilter', placeholder='ДД',
                                     style={'width':'100%','margin-right': '6px', 'display': 'inline-block'},
                                     disabled=True,
                                     options=options['day'] + [
                                         {'label': '✱', 'value': 'Все'}]),
                    ], width=4),
                    dbc.Col([
                        dcc.Dropdown(id='MonthFilter', placeholder='ММ',
                                     style={'width':'100%', 'margin-right': '6px', 'display': 'inline-block'},
                                     disabled=True,
                                     options=options['month'] + [
                                         {'label': '✱', 'value': 'Все'}], ),
                    ], width=4),
                    dbc.Col([
                        dcc.Dropdown(id='YearFilter', placeholder='ГОД', style={'width':'100%', 'margin-right': '6px','display':'inline-block'},
                                     options=options['year'] + [
                                         {'label': '✱', 'value': 'Все'}], ),
                    ], width=4),

                    ], className='g-1' )
                ]),
                dbc.Row([
                    dbc.Col([
                    dcc.Dropdown(id='UserFilter',placeholder='Сотрудник',
                                 options=[{'label': '[Все сотрудники]', 'value': 'Все'}] + options['user']),
                    dcc.Dropdown(id='ProjectFilter',placeholder='Проект',
                                 options=[{'label': '[Все проекты]', 'value': 'Все'}] + options['project']),
                    dcc.Dropdown(id='StageFilter',placeholder='Этап',
                                 options=options['stage']+[{'label': '[Все Этапы]', 'value': 'Все'}]),
                    dcc.Dropdown(id='SquareFilter', placeholder='Площадь',
                                     options=options['square'] + [{'label': '[Все]', 'value': 'Все'}]),
                    dcc.Dropdown(id='RelevantFilter', placeholder='Актуальность',
                                 options=[{'label': 'Только актуальные', 'value': 1},{'label': 'Только завершенные', 'value': 0,}]),
                    ]),
                ]),
        ], className='cloud', style={'margin-bottom':'0', 'padding-bottom':'14px', 'min-width':'260px'}),
        html.Button('Сбросить', className='clean', id='refresh')
        ], className='filters line'),
        html.Div([],id='RowCount', className='cloud number rows'),
    ])
    return content

from dash import dcc, html
import dash_bootstrap_components as dbc

def ADMINPAGE():
    content = html.Div([
        dcc.ConfirmDialog(
            id='ConfirmDelete',
            message='Внимание!',
        ),
        html.Div([
            html.Div('АДМИНИСТРИРОВАНИЕ', className='line name'),
            html.Div([
                html.Div([], id='popupAdm', className='line')
            ], id='popupBoxAdm', className='line'),
        ], className='line-wrap', style={'margin-bottom': '0', 'position': 'relative'}),

        html.Div([
            dcc.Tabs(id='tabs', value='tab-c', children=[
                dcc.Tab(label='Сотрудники', value='tab-c', className='custom-tab',
                        selected_className='custom-tab--selected'),
                dcc.Tab(label='Проекты', value='tab-p', className='custom-tab',
                        selected_className='custom-tab--selected'),
            ], parent_className='custom-tabs', className='custom-tabs-container'),
        ], className='cloud tablo'),

        dcc.Loading([html.Div(id='tabs-content')], color='grey', type='circle'),

        html.Div([
            html.Button('✏️ Редактировать', id='EditButton', className='button edit line cloud', style={'display': 'none'}),
            html.Button('+Новый', className='clean add line', id='AddButton'),
            html.Button('📄 Скачать логи', id='DownloadLogsBtn', className='clean dwnld line'),
            dcc.Download(id="DownloadLogs")
        ], className='line-wrap'),


        # Модалка
        dbc.Modal(
            [
                dbc.ModalHeader([]),
                dbc.ModalBody([
                    dcc.Input(id='UserName', placeholder='Имя сотрудника', className='inp'),
                    dcc.Input(id='UserLogin', placeholder='Логин', className='inp'),
                    dcc.Input(id='UserPass', placeholder='Пароль', className='inp'),
                    dbc.Label("Роль", html_for="slider"),
                    dcc.Slider(id="UserRole", min=0, max=1, step=1, marks={0: 'Юзер', 1: 'Админ'}),
                    dcc.Checklist(id='UserActual', className='check',
                                  options=[{'label': 'Актуальный', 'value': '1'}])
                ], style=dict(paddingLeft=16)),
                dbc.ModalFooter([
                    dbc.Button("Удалить", id="ModalDelete", className="button cloud delete", n_clicks=0),
                    dbc.Button("Применить", id="ModalSubmit", className="button cloud submit", n_clicks=0)
                ]),
            ],
            id="DialogModal",
            centered=True,
            is_open=False,
        ),
    ])
    return content

