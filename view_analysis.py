from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from utils import rgba_string_to_hex
from datetime import datetime
import pandas as pd
from app import cache
import db
import plotly.graph_objs as go

# Пример входных данных
employee_data = {
    'АЛЕКСЕЙ': {13: 3, 14: 1, 15: 4, 16: 6, 17: 2, 18: 5},  # день: часы
    'ЮЛИЯ': {9: 4, 10: 6,},
    'МАРИАМ': {4: 2, 6: 3, 7: 4, 8: 5, 9: 5, 10: 4},
    'АННА': {10: 3, 12: 2, 13: 3, 14: 5, 15: 6}
}

color_map = {
    'АЛЕКСЕЙ': '#FFD700',
    'ЮЛИЯ': '#90EE90',
    'МАРИАМ': '#FFB6C1',
    'АННА': '#87CEFA',
}
data = [
    {"Этап": "ПОДГОТОВКА", "АЛЕКСЕЙ": 25, "ЮЛИЯ": 24, "МАРИАМ": 13, "АННА": 8},
    {"Этап": "3D ГРАФИКА", "АЛЕКСЕЙ": 8, "ЮЛИЯ": 6, "МАРИАМ": 33, "АННА": 0},
    {"Этап": "ЗАКАЗНЫЕ ПОЗИЦИИ", "АЛЕКСЕЙ": 0, "ЮЛИЯ": 0, "МАРИАМ": 0, "АННА": 16},
    {"Этап": "СМР", "АЛЕКСЕЙ": 0, "ЮЛИЯ": 0, "МАРИАМ": 0, "АННА": 0},
    {"Этап": "КОМПЛЕКТАЦИЯ", "АЛЕКСЕЙ": 0, "ЮЛИЯ": 0, "МАРИАМ": 0, "АННА": 0},
    {"Этап": "РЕАЛИЗАЦИЯ", "АЛЕКСЕЙ": 0, "ЮЛИЯ": 0, "МАРИАМ": 0, "АННА": 0},
]
color_map = {
    "АЛЕКСЕЙ": "#FFD700",  # жёлтый
    "ЮЛИЯ": "#32CD32",     # зелёный
    "МАРИАМ": "#FF69B4",   # розовый
    "АННА": "#87CEFA",     # голубой
    "ИТОГО": "#d9d9d9"
}

style_header_conditional = [
    {
        "if": {"column_id": name},
        "backgroundColor": color,
        "color": "black",

    }
    for name, color in color_map.items()
]
# Создание DataFrame
df = pd.DataFrame(data)
df["ИТОГО"] = df[["АЛЕКСЕЙ", "ЮЛИЯ", "МАРИАМ", "АННА"]].sum(axis=1)

# Добавление строки с итогами по каждому сотруднику
totals = {
    "Этап": "",
    "АЛЕКСЕЙ": df["АЛЕКСЕЙ"].sum(),
    "ЮЛИЯ": df["ЮЛИЯ"].sum(),
    "МАРИАМ": df["МАРИАМ"].sum(),
    "АННА": df["АННА"].sum(),
    "ИТОГО": df["ИТОГО"].sum()
}
df.loc[len(df.index)] = totals



def GRAPHIC(project_id):
    today = datetime.today()
    options = db.get_graph_filters()
    p = db.get_project_full(project_id)
    prj_data = dict(
        Title=p[1],
        PrjName=p[1],
        PrjSqr=p[2],
        PrjLvl=p[3],
        PrjStart=p[4],
        PrjDone=p[5],
    )
    content = html.Div([
        html.Div(prj_data['Title'].upper(), className='name', id='BigTitle'),
        html.Div([
                dcc.Loading([
                    html.Div([
                        dcc.Graph(
                            id='Graph',
                            # figure=generate_graph(project_id, 7, 2025),
                            config={"displayModeBar": False,},
                            style={'height': '400px'}  # фиксируем только высоту
                        )
                    ],className='cloud' , style={
                        'width': '94%',
                        'max-width': '1320px',
                        'padding': '10px 30px 10px 0',  # отступы слева и справа
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
                                    dcc.Dropdown(id='ProjectFilterGraph', placeholder='Проект',
                                                 options=options['project'], value=project_id),
                                    dcc.Dropdown(id='YearFilterGraph', placeholder='Год',
                                                 options=options['year'], value=today.year),
                                    dcc.Dropdown(id='MonthFilterGraph', placeholder='Месяц',
                                                 options=options['month'], value=today.month),
                                ]),
                            ]),
                        ], className='cloud',
                            style={'margin-bottom': '0', 'padding-bottom': '14px', 'min-width': '260px'}),
                        html.Button('Сбросить', className='clean w100', id='refresh')
                    ], className='filters line'),
                ], width="auto"),
                dbc.Col([
                    html.Div([
                        dcc.Loading([
                            dash_table.DataTable(
                                id='TableGraph',
                                fixed_rows={'headers': True, },
                                columns=[{"name": col, "id": col} for col in df.columns],
                                data=df.to_dict("records"),

                                style_data={
                                    'whiteSpace': 'normal'
                                },
                                style_table={
                                    'overflow': 'hidden',
                                    'margin': '0',
                                    'margin-top': '0px',
                                    'padding': '0',
                                    'width': '100%',
                                    'height': 'fit-content',

                                    'min-width': '600px',
                                    'max-height': '300px',
                                    'overflow-y': 'auto',
                                    'border': '0px solid white',
                                    'borderRadius': '10px',
                                    'transition': 'all 0.12s ease-in-out',
                                },
                                style_cell={'font-family': 'Rubik', 'text-align': 'left', 'width': 'auto',
                                            'border': '2px solid white', 'background-color': '#f7f7f7',
                                            'font-size': '14px', 'padding-left': '6px', 'cursor': 'default'},
                                style_header={'background-color': '#313131', 'color': 'white', 'height': '30px','z-index': '5',
                                              'border': '0px solid white', 'border-right': '2px solid white','border-left': '2px solid white', 'font-family': 'Rubik', 'font-size': '13px',
                                              'padding-left': '2px', },
                                style_header_conditional= style_header_conditional,
                                style_cell_conditional=[
                                                           {
                                                               'if': {'column_id': 'Этап'},

                                                               'background-color': '#EAEAEA',
                                                               # 'padding': '0',
                                                               'width': '180px',
                                                               'max-width': '180px',
                                                           },
                                                            {
                                                                'if': {'column_id': 'ИТОГО'},

                                                                # 'background-color': '#EAEAEA',
                                                                # 'padding': '0',
                                                                'width': '65px',
                                                                'max-width': '65px',
                                                            },
                                                            {
                                                                'if': {'row_index': len(df) - 1},
                                                                'backgroundColor': '#EAEAEA',  # Тёмно-серый
                                                            },
                                                            {
                                                                'if': {'column_id': df.columns[-1]},
                                                                'backgroundColor': '#EAEAEA',
                                                            }

                                                       ]
                            )], color='grey', type='circle'),
                    ], className='cloud graph')
                ], width="auto"),
            ], className='g-1'),

        ], style={'width':'100%'}),
    ])
    return content
