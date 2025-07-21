from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from utils import rgba_string_to_hex, month_name_ru
from datetime import datetime
from plotly.graph_objs import Figure, Bar, Layout
import flask_login
import pandas as pd
from app import cache
import db
import plotly.colors as pc
import plotly.graph_objs as go

def GRAPHIC(id=None, is_project=False):
    today = datetime.today()
    options = db.get_graph_filters()
    if not is_project and not id:
        id = flask_login.current_user.id

    content = html.Div([
        dcc.Store(id='GraphMode', data=1 if is_project else 0),
        html.Div('', className='name', id='BigTitle'),
        html.Div([
                dcc.Loading([
                    html.Div([
                        dcc.Graph(
                            id='Graph',
                            # figure=generate_graph(project_id, 7, 2025),
                            config={"displayModeBar": False,},
                            style={'height': '400px',}  # фиксируем только высоту
                        )
                    ],className='cloud' , style={
                        'width': '94%',
                        'max-width': '1320px',
                        'padding': '10px 20px 5px 0',  # отступы слева и справа
                        'box-sizing': 'border-box'
                    })
            ], ),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Div('Настройки',
                                     style={'margin-bottom': '8px', 'margin-top': '8px', 'font-weight': '700px',
                                            'font-size': '16px', 'color': 'black'}),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Dropdown(id='FilterGraph', placeholder='Проект',
                                                 options=options['project'] if is_project else options['user'], value=id, clearable=False),
                                    dcc.Dropdown(id='YearFilterGraph', placeholder='Год',
                                                 options=options['year'], value=today.year, clearable=False),
                                    dcc.Dropdown(id='MonthFilterGraph', placeholder='Месяц',
                                                 options=options['month'], value=today.month),
                                ]),
                            ]),
                        ], className='cloud',
                            style={'margin-bottom': '0', 'padding-bottom': '14px', 'min-width': '260px'}),
                        html.Button('Сбросить', className='clean w100', id='RefreshGraph')
                    ], className='filters line'),
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        dcc.Loading([
                            dash_table.DataTable(
                                id='GraphTable',
                                fixed_rows={'headers': True, },
                                # fill_width=True,
                                cell_selectable=False,
                                style_data={
                                    'whiteSpace': 'normal'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {
                                            'row_index': 6
                                        },
                                        'backgroundColor': '#f0f0f0',
                                    }
                                ],
                                style_table={
                                    'overflow': 'hidden',
                                    'margin': '0',
                                    'margin-top': '0px',
                                    'padding': '0',
                                    'width': '100%',
                                    'height': 'fit-content',

                                    'min-width': '600px' if is_project else '420px',
                                    'max-height': '300px',
                                    'overflow-y': 'auto',
                                    'border': '0px solid white',
                                    'borderRadius': '10px',
                                    'transition': 'all 0.12s ease-in-out',
                                    'overflowX': 'auto'
                                },
                                style_cell={'font-family': 'Rubik', 'text-align': 'left', 'min-width': '70px',
                                            'border': '2px solid white', 'background-color': '#f7f7f7','whiteSpace': 'nowrap','overflow': 'hidden','textOverflow': 'ellipsis',
                                            'font-size': '14px', 'padding-left': '6px', 'cursor': 'default', },
                                style_header={'background-color': '#646464', 'color': 'white', 'height': '30px','z-index': '5',
                                              'border': '0px solid white', 'border-right': '2px solid white',
                                              'border-left': '2px solid white','border-bottom': '1px solid white', 'font-family': 'Rubik', 'font-size': '13px',
                                              'padding-left': '2px', 'whiteSpace': 'nowrap',
                                                'overflow': 'hidden', 'max-width':'150px' if not is_project else 'auto',
                                                'textOverflow': 'ellipsis',
                                                  # <-- обязательно с единицами
                                                'textAlign': 'left'},
                                style_cell_conditional=[
                                                           {
                                                               'if': {'column_id': 'index'},

                                                               # 'background-color': '#f0f0f0',
                                                               'background-color': '#f0f0f0',
                                                               'width': '180px',
                                                               'max-width': '180px',
                                                           } if is_project else
                                                           {
                                                               'if': {'column_id': 'index'},

                                                               # 'background-color': '#f0f0f0',
                                                               'background-color': '#f0f0f0',
                                                               'width': '50px',
                                                               'max-width': '50px',
                                                           },
                                                            {
                                                                'if': {'column_id': 'Σ'},

                                                                'background-color': '#f0f0f0',
                                                                'width': '65px',
                                                                'max-width': '65px',
                                                            },

                                                       ]
                            )], color='grey', type='circle'),
                    ], className='cloud graph')
                ], width="auto"),
            ], className='g-1'),

        ], style={'width':'100%'}),
    ])
    return content



def GANTT():
    today = datetime.today()
    options = db.get_graph_filters()
    palette_names = ['Aggrnyl', 'Viridis', 'Cividis', 'Plasma', 'Magma', 'Purpor', 'Turbo', 'Sunset']

    # Палитры
    palette_options = []
    for name in palette_names:

        scale = getattr(pc.sequential, name)
        samples = [pc.sample_colorscale(scale, i / 4) for i in range(5)]

        swatch = html.Span([
            html.Span(style={
                'display': 'inline-block',
                'width': '12px',
                'height': '12px',
                'backgroundColor': color,
                'marginRight': '2px',
                'borderRadius': '2px',

            }) for color in samples
        ])

        palette_options.append({
            'label': html.Div([swatch, html.Span(f'  {name if name != "Aggrnyl" else "Seaweed"}', style={'margin-left':'8px'})], style={'display': 'flex', 'alignItems': 'center'}),
            'value': name
        })


    content = html.Div([
        html.Div('ДИАГРАММА ГАНТА', className='name', id='BigTitle'),
        html.Div([
            dcc.Loading([
                html.Div([
                    dcc.Graph(
                        id='GraphGantt',
                        # figure=gantt_figure,
                        config={"displayModeBar": False},
                        # style={'height': '400px'}
                        style={'height': 'auto'}
                    )
                ], className='cloud', style={
                    'width': '94%',
                    'max-width': '1320px',
                    'padding': '10px 20px 5px 0',
                    'box-sizing': 'border-box'
                })
            ],  color='#1a1a1a', type='circle',
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},fullscreen=False,
            custom_spinner=html.H3(["Загрузка ", dbc.Spinner(color="#1a1a1a")], className='LoadingSpinner'),
            ),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.Div('Настройки',
                                     style={'margin-bottom': '8px', 'margin-top': '8px', 'font-weight': '500',
                                            'font-size': '16px', 'color': 'black'}),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Dropdown(id='YearFilterGantt', placeholder='Год',
                                                 options=options['year'], value=today.year, clearable=False),
                                    dcc.Dropdown(id='RelevantFilterGantt', placeholder='Актуальность',
                                                 options=[{'label': 'Только актуальные', 'value': 1},
                                                          {'label': 'Только завершенные', 'value': 0, }], ),
                                ]),
                            ]),
                        ], className='cloud',
                            style={'margin-bottom': '0', 'padding-bottom': '14px', 'min-width': '260px'}),
                        # html.Button('Сбросить', className='clean w100', id='RefreshGraph')
                    ], className='filters line'),
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        html.Div('Цветовая палитра',
                                 style={'margin-bottom': '8px', 'margin-top': '8px', 'font-weight': '500',
                                        'font-size': '16px', 'color': 'black'}),
                        dcc.Dropdown(
                            id='PaletteFilterGantt',
                            placeholder='Цвета',
                            options=palette_options,
                            value='Aggrnyl',
                            clearable=False,
                        )
                    ], className='cloud',
                        style={'margin-bottom': '0', 'padding-bottom': '14px', 'min-width': '250px'}),
                ], width="auto"),
            ], className='g-1'),
        ], style={'width': '100%'}),
    ])
    return content


