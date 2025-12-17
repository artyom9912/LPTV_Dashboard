import pandas as pd
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
from utils import to_css_rgba
import db
from app import appDash, engine
import dash


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
                }
style_cell={'font-family': 'Rubik', 'text-align': 'left', 'width':'auto',
            'border': '3px solid white', 'background-color': '#f7f7f7',
            'font-size': '14px', 'padding-left':'12px','cursor':'pointer'}
style_header={'background-color': '#E1E1E1', 'color': 'black', 'height': '35px','z-index':'5','padding-left':'6px',
              'border': '0px solid white', 'font-family': 'Rubik', 'font-size': '14px','cursor':'default'}
def get_style_data_conditional():
    return [
        {
            'if': {
                'filter_query': '{СТАТУС} eq "Актуальный"',
                'column_id': 'СТАТУС'
            },
            # 'color': '#25c193'
            'color': '#3DA476'
        },
        {
            'if': {
                'filter_query': '{СТАТУС} eq "Не актуальный"',
                'column_id': 'id'
            },
            # 'color': '#25c193'
            'backgroundColor': '#f7f7f7'
        },
        {
            'if': {
                'filter_query': '{СТАТУС} eq "Не актуальный"',
                'column_id': 'СТАТУС'
            },
            'color': 'silver'
        },
        {
            "if": {"state": "selected"},  # 'active' | 'selected'
            "backgroundColor": "rgba(0, 116, 217, 0.3)",
            'border': '3px solid white',
        },
        {
            'if': {'column_id': 'id'},
            'width': '36px',
        }
        ,
        {
            'if': {'column_id': 'НАЗВАНИЕ'},
            'padding-left': '22px',
        }
    ]
style_data_conditional = get_style_data_conditional()



def UsersTable():
    content = html.Div([
        dash_table.DataTable(
            id='AdmTable',
            style_table = style_table,
            style_cell= style_cell,
            style_header=style_header,
            fixed_rows={'headers': True, 'data': 0},
            style_as_list_view=True,
        )
    ], style={'height':'100%'})
    return content

def ProjectsTable():
    content = html.Div([
        dash_table.DataTable(
            id='AdmTable',
            sort_action="native",
            style_table=style_table,
            style_cell=style_cell,
            style_header=style_header,
            fixed_rows={'headers': True, 'data': 0},
            style_as_list_view=True,
        )
    ], style={'height':'100%'})
    return content


@appDash.callback(
    Output("AdmTable", "data"),
    Output("AdmTable", "columns"),
    Input("tabs", "value"),
)
def AdmTableContent(tab):
    if tab == 'tab-c':
        df = db.get_users()
        df.columns = ['id', 'ИМЯ', 'ЛОГИН', 'ЦВЕТ', 'АДМИН', 'СТАТУС']
        df['АДМИН'] = df['АДМИН'].map(lambda x: 'Да' if x == 1 else 'Нет')
        df['СТАТУС'] = df['СТАТУС'].map(lambda x: 'Актуальный' if x == 1 else 'Не актуальный')
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]
    elif tab == 'tab-p':
        df = db.get_projects()
        df.columns = ['id', 'НАЗВАНИЕ', 'M²', 'СТАРТ', 'СТАТУС']
        df['СТАТУС'] = df['СТАТУС'].map(lambda x: 'Актуальный' if x == 0 else 'Не актуальный')
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]


# noinspection PyTypeChecker
@appDash.callback(
    Output("AdmTable", "style_data_conditional"),
    Input("AdmTable", "active_cell"),
    Input("tabs", "value"),
    Input("AdmTable", "data"),
)
def style_selected_rows(sel_rows, tab, data):
    if sel_rows is None:
        if tab == 'tab-c':
            style = style_data_conditional
            df = pd.DataFrame.from_records(data)
            for i, rgba in enumerate(df["ЦВЕТ"]):
                rgba_str = to_css_rgba(rgba)
                style.insert(0,{
                    'if': dict(row_index=i, column_id='id'),
                    'backgroundColor': rgba_str,
                    'color': 'black'
                })
            print(style)
            return style
        else:
            style = get_style_data_conditional()
            print(style)
            return style
    val = [
        {"if": {"filter_query": "{{id}} ={}".format(sel_rows['row_id'])}, "backgroundColor": "rgba(0, 116, 217, 0.3)", }
        for i in sel_rows
    ]
    if tab == 'tab-p':
        return get_style_data_conditional()+val
    else:
        return style_data_conditional + val

    # return [sel_rows['row_id']]

@appDash.callback(
    Output("AdmTable", "derived_virtual_selected_row_ids"),
    Input("AdmTable", "active_cell"),
)
def select_cell(cell):
    if cell is None:
        return dash.no_update
    print([cell['row_id']])
    return [cell['row_id']]

@appDash.callback(
    Output("EditButton", "style"),
    Input("AdmTable", "active_cell"),
    prevent_initial_call = True
)
def show_button(cell1):
    if cell1 is None:
        return {'display':'none'}
    return {'display':'inline-block'}

