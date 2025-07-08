import datetime
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dash import dcc
from dash.dependencies import Input, Output, State
# from app import appDash, calendar_cache, WEEKDAYS, engine, dbDF, cache
import db
from app import appDash, engine, cache
import dash
from utils import get_user_picture, rgba_string_to_hex, hex_to_rgba01
from time import sleep
from dash import html
from datetime import date
from logger import logger
import traceback
import sys
import plotly.graph_objects as go
import flask_login
from datatables import UsersTable, ProjectsTable, to_css_rgba

# WEEK_NUMBERS = dict(zip(WEEKDAYS, range(0, 7)))
CACHE = {}



@appDash.callback(
    Output('USER', 'children'),
    Output('ROLE', 'children'),
    Output('UserPic', 'src'),
    Input('content', 'children')
)
def SetUser(style):
    user = flask_login.current_user
    return user.name, 'Администратор' if user.admin == 1 else 'Сотрудник', get_user_picture(db.get_user_login(user.name))

@appDash.callback(
    Output('ProjectDesk', 'children'),
    Input('RelevantFilterDesk', 'value'),
    Input('YearFilterDesk', 'value'),
)
def UpdateProjectDesk(relevant, year):
    projects = db.get_project_cards(relevant, year)
    content = [html.Div([
                html.Div([project['name'], html.Div([dcc.Markdown(str(project['square']) + " m²", className='prjStage'),]),],
                         className='prjName'),

                html.Div([
                    html.Div([project['sum_hours'], html.Span('часов', className='tail')], className='num line'),
                    html.Div([project['count_users'], html.Span('чел.', className='tail')], className='num line dim'),
                    html.Div([project['level']], className='num line last'),
                ], className='line-wrap prjInfo', style={'background':'linear-gradient(to right, rgba(243, 243, 243, 0) 210px, #E1D2BEFF 20px)'} if project['isDone']==1 else {}),
              ], className='card', style={'border-color':'#E1D2BEFF'} if project['isDone']==1 else {}) for id, project in projects.iterrows()]
    return content

@cache.memoize()
@appDash.callback(
    Output('MonthFilter', 'disabled'),
    Output('DayFilter', 'disabled'),
    Input('DayFilter', 'value'),
    Input('MonthFilter', 'value'),
    Input('YearFilter', 'value'),
    prevent_initial_call=True
)
def update_db( day, month, year):
    if year is not None:
        if month is not None:
            return False, False
        else:
            return False, True
    else:
        return False, False


@appDash.callback(
    Output('UserFilter', 'value'),
    Output('ProjectFilter', 'value'),
    Output('StageFilter', 'value'),
    Output('DayFilter', 'value'),
    Output('MonthFilter', 'value'),
    Output('YearFilter', 'value'),
    Output('SquareFilter', 'value'),
    Input('refresh', 'n_clicks'),
    prevent_initial_call=True
)
def clean_filter(n_clicks):
    return None, None, None, None, None, None, None


@appDash.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'))
def render_content(tab):
    match tab:
        case 'tab-c':
            return html.Div([
                UsersTable()
            ], className='db')
        case 'tab-p':
            return html.Div([
                ProjectsTable()
            ], className='db')

#
#
# calendar = None
#
#
# @appDash.callback(
#     Output('Datepicker', 'date'),
#     Output('EndDate', 'children'),
#     Output('CalendarTable', 'data'),
#     Output('CalendarTable', 'columns'),
#     Output('AddProjectCal', 'value'),
#     Input('AddProjectCal', 'value'),
#     Input('Datepicker', 'date'),
# )
# def SetDatesCalendar(addProject, start_date):
#     con = engine.connect()
#     # con = connect('clickhouse://10.200.2.113')
#     try:
#         start_date = dt.strptime(start_date, '%Y-%m-%d')
#     except:
#         start_date = dt.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
#     weekday = int(start_date.weekday())
#     start = start_date + datetime.timedelta(days=-1 * weekday)
#     end = start_date + datetime.timedelta(days=6 - weekday)
#     # В ЦИКЛЕ СОБИРАЕМ ВСЕ ДНИ НЕДЕЛИ
#     for i in range(0, 7):
#         day = (start + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
#         # СБОР ДАННЫХ КАЛЕНДАРЯ (ПРИСОЕДИНЕНИЕ ЧЕРЕЗ WHERE)
#         df = pd.read_sql \
#             (f"""
#             SELECT title, timestamp, hours FROM skameyka.main_table m, skameyka.project_table p
#             WHERE m.timestamp = '{day}' AND user_id = (SELECT id FROM user_table WHERE fullname like '{flask_login.current_user.name}')
#             AND m.project_id = p.id;
#         """, con)
#         df = df.drop('timestamp', axis=1)
#         df.columns = ['НАЗВАНИЕ ПРОЕКТА', WEEKDAYS[i]]
#
#         if i == 0:
#             calendar = df
#         else:
#             calendar = calendar.merge(df, on='НАЗВАНИЕ ПРОЕКТА', how='outer')
#     if addProject is not None:
#         newdf = pd.DataFrame({'НАЗВАНИЕ ПРОЕКТА': [addProject], 'ПН': [None], 'ВТ': [None], 'СР': [None], 'ЧТ': [None], 'ПТ': [None], 'СБ': [None], 'ВС': [None]})
#         calendar = pd.concat([calendar,newdf])
#     columns = [{"name": i, "id": i} for i in ['НАЗВАНИЕ ПРОЕКТА'] + WEEKDAYS]
#     columns[0]['editable'] = False
#
#     return start, end.strftime('%d.%m.%Y'), calendar.to_dict('records'), columns, None
#
# @appDash.callback(
#     Output('popup', 'children'),
#     Input('CalendarSave', 'n_clicks'),
#     State('popup', 'children'),
#     prevent_initial_call=True
# )
# def SaveCalendar(n_clicks, old):
#     con = engine.connect()
#     # con = connect('clickhouse://10.200.2.113')
#     if len(calendar_cache) == 0:
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [
#             html.Div([html.Span('😬', className='symbol emoji'), 'Нет изменений'], className='cloud line popup white',hidden=False)]
#     try:
#         for sql in calendar_cache:
#             con.execute(text(sql))
#         con.commit()
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [html.Div([html.Span('✔', className='symbol'), 'Успешно сохранено'], className='cloud line popup green', hidden=False)]
#
#     except Exception as e:
#         e_type, e_val, e_tb = sys.exc_info()
#         traceback.print_exception(e_type, e_val, e_tb, file=open('log.txt', 'a'))
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [html.Div([html.Span('😧', className='symbol emoji'), 'Возникла ошибка!'], className='cloud line popup orange', hidden=False)]
#
#
#
# @appDash.callback(
#     Output('popupBox', 'children'),
#     Input('popup', 'children'),
#     prevent_initial_call=True
# )
# def SaveCalendar(ch):
#     if len(ch) != 0:
#         sleep(2.5)
#         return html.Div([], id='popup', className='line')
#     else:
#         dash.no_update()
#
#
# @appDash.callback(
#     Output('pie-chart', 'figure'),
#     Output('pie-chart', 'style'),
#     Input('CalendarTable', 'data'),
# )
# def UpdatePie(data):
#     global calendar
#     calendar = pd.DataFrame(data)
#     if calendar.empty:
#         style = dict(display='none')
#         return dash.no_update, style
#     else:
#         style = dict(visibility='visible')
#         calendar[WEEKDAYS] = calendar[WEEKDAYS].apply(pd.to_numeric)
#
#     # calendar.info()
#     colors = ['#393E46', '#00ADB5', '#AAD8D3', '#EEEEEE', '#8ee8e4', '#F3F4ED', '#30475E', '4CA1A3']
#     mart = calendar.fillna(0)
#
#     # print(style)
#     mart['sum'] = mart['ПН'] + mart['ВТ'] + mart['СР'] + mart['ЧТ'] + mart['ПТ'] + mart['СБ'] + mart['ВС']
#     mart = mart[['НАЗВАНИЕ ПРОЕКТА', 'sum']]
#     labels = mart['НАЗВАНИЕ ПРОЕКТА'].tolist()
#     values = mart['sum'].tolist()
#     # print(mart)
#     # print(mart.info())
#     fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
#     fig.update_traces(automargin=False, selector=dict(type='pie'),
#                       marker=dict(colors=colors), textfont_size=12,
#                       hoverinfo='label+percent', textinfo='none')
#     fig.update_layout(
#         font_family="Roboto",
#         font_color="black",
#         font_size=16,
#         margin=dict(l=4, r=12, t=20, b=40),
#         height=280,
#         width=410,
#         legend=dict(font=dict(family="Rubik", size=12, color="black")),
#         hoverlabel=dict(
#             font_size=14,
#             font_family="Rubik",
#         )
#     )
#     return fig, style
#
#
# @appDash.callback(
#     Output('CalendarSave', 'style'),
#     [Input('CalendarTable', 'data')],
#     [State('CalendarTable', 'data_previous')],
#     [State('Datepicker', 'date')],
#     prevent_initial_call=True
# )
# def CalendarChanges(current, previous, start_date):
#
#     if previous is None: return dash.no_update
#     total = []
#     i = 0
#     for project in current:
#         old_project = previous[i]
#         i += 1
#         diff = [[k, project[k]] for k in project if k in old_project and project[k] != old_project[k]]
#         if len(diff) != 0:
#             if old_project[diff[0][0]] is None: status = 'INS'
#             elif project[diff[0][0]] == '0' or project[diff[0][0]] is None: status = 'DEL'
#             else: status = 'UPD'
#             total.append([project['НАЗВАНИЕ ПРОЕКТА']] + diff[0]+[status])
#             break
#     UPDATE = total[0]
#
#     user = flask_login.current_user.name
#
#     start_date = dt.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
#     date = start_date + datetime.timedelta(days=WEEK_NUMBERS[UPDATE[1]])
#     date = date.strftime('%Y-%m-%d')
#     # КУЧА ПОДЗАПРОСОВ CRUD
#     if UPDATE[3] == 'UPD':
#         query = f"""
#                 UPDATE skameyka.main_table SET hours = {UPDATE[2]} WHERE user_id =
#                 (SELECT id FROM skameyka.user_table WHERE fullname like '{user}')
#                 AND project_id =
#                 (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}')
#                 AND timestamp = '{date}'
#         """
#     elif UPDATE[3] == 'DEL':
#         query = f"""
#                 DELETE FROM skameyka.main_table WHERE user_id =
#                 (SELECT id FROM skameyka.user_table WHERE fullname like '{user}')
#                 AND project_id =
#                 (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}')
#                 AND timestamp = '{date}'
#         """
#     else:
#         query = f"""
#                 INSERT INTO skameyka.main_table (user_id, project_id, timestamp, hours) VALUES
#                 (
#                     (SELECT id FROM skameyka.user_table WHERE fullname like '{user}'),
#                     (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}'),
#                     '{date}', {UPDATE[2]}
#                 )
#                 """
#     calendar_cache.append(query)
#
#     return dash.no_update

@appDash.callback(
    Output("TableDB", "data"),
    Output("TableDB", "columns"),
    Output("TableDB", "page_size"),
    Output("TableDB", "page_action"),
    Output("RowCount", "children"),
    Input("TableDB", "page_current"),
    Input("TableDB", "page_size"),
    Input('UserFilter', 'value'),
    Input('ProjectFilter', 'value'),
    Input('SquareFilter', 'value'),
    Input('StageFilter', 'value'),
    Input('DayFilter', 'value'),
    Input('MonthFilter', 'value'),
    Input('YearFilter', 'value'),
)
def update_table(page_current, page_size, user, project, square, stage, day, month, year):
    HEAD_MAP = {
        'year': 'ГОД',
        'month': 'ММ',
        'day': 'ДД',
        'user': 'СОТРУДНИК',
        'project': 'ПРОЕКТ',
        'stage': 'ЭТАП',
        'square': 'м²',
        'hours': 'ЧАСЫ'
    }

    field_map = {
        'year': [year, 'YEAR(dateStamp) year', None, 'YEAR(dateStamp)'],
        'month': [month,'MONTH(dateStamp) month', None, 'MONTH(dateStamp)'],
        'day': [day,'DAY(dateStamp) day', None, 'DAY(dateStamp)'],
        'user': [user, 'u.name user', 'JOIN user u ON main.userId=u.id\n', 'u.name'],
        'project': [project, 'p.name project', 'JOIN project p ON main.projectId=p.id\n', 'p.name'],
        'square': [square, 'p.square square', 'JOIN project p ON main.projectId=p.id\n', 'p.square'],
        'stage': [stage, 's.name stage', 'JOIN stage s ON main.stageId=s.id\n', 's.name'],
    }

    # Если ни один фильтр не выбран — показать "сырые" данные
    if all(v[0] is None for v in field_map.values()):
        data, columns = db.get_db_chunk(page_current, page_size)
        page_size= 40
        page_action='custom'
        count = db.get_main_count()


    else:
        page_size = 250
        page_action = 'native'

        # Фильтрация и группировка по выбранным
        select_keys = [field_map[k][1] for k, v in field_map.items() if v[0] is not None]
        group_by_keys = [k for k, v in field_map.items() if v[0] is not None]
        filters = [f"{field_map[k][-1]} = '{v[0]}'" for k, v in field_map.items() if v[0] is not None and 'Все' != v[0] ]
        joins = [field_map[k][2] for k, v in field_map.items() if v[0] is not None and v[2] is not None]
        order = [k+" DESC" for k, v in list(field_map.items())[:3] if v[0] is not None]

        select_clause = ', '.join(select_keys)
        where_clause = " AND ".join(filters) if filters else "1=1"
        join_clause = ''.join(list(set(joins))) if len(joins) > 0 else ''
        group_by_clause = ', '.join(group_by_keys)
        order_by_clause = ', '.join(order)
        order_by_clause+= ',' if len(order_by_clause) > 0 else ''
        data, columns = db.get_filtered_data(select=select_clause ,group_by=group_by_clause,
                                             filters=where_clause, join=join_clause, order_by=order_by_clause)
        count = len(data)

    # Формирование колонок таблицы
    column_defs = [{"name": HEAD_MAP.get(col, col.upper()), "id": col} for col in columns]
    return data, column_defs, page_size, page_action, [count, html.Span('кол. строк', className='tail')]





from dash.exceptions import PreventUpdate
import logging

logger = logging.getLogger(__name__)

@appDash.callback(
    Output('DialogModal', 'children'),
    Output('DialogModal', 'is_open'),
    [State("tabs", "value"),
     State("AdmTable", "derived_virtual_selected_row_ids")],
    [Input('EditButton', 'n_clicks'),
     Input('AddButton', 'n_clicks'),
     Input('ModalSubmit', 'n_clicks'),
     Input('ModalDelete', 'n_clicks')],
    prevent_initial_call=True
)
def RenderModal(tab, row, clickE, clickA, clickS, clickD):
    try:
        changed_id = dash.callback_context.triggered[0]['prop_id']
        UPDATE_DICT = 'EditButton' in changed_id
        Open = 'EditButton' in changed_id or 'AddButton' in changed_id

        if 'ModalSubmit' in changed_id or 'ModalDelete' in changed_id:
            return dash.no_update, False

        CACHE.clear()
        id = row[0] if row else None
        CACHE['id'] = id

        if tab == 'tab-c':
            if UPDATE_DICT:
                u = db.get_user_full(id)
                user_data = dict(
                    Title=u[1].upper(),
                    Span=f'ID: {id}',
                    UserName=u[1],
                    UserLogin=u[2],
                    UserRole=u[3],
                    UserActual=u[4],
                    UserColor=u[5],
                    UserPass=u[6]
                )
            else:
                user_data = dict(
                    Title='НОВЫЙ ЮЗЕР',
                    Span='',
                    UserName=None,
                    UserLogin=None,
                    UserPass=None,
                    UserRole=0,
                    UserActual=1,
                    UserColor='0.3,0.3,0.3,1'
                )

            modal = [
                dbc.ModalHeader(
                    [user_data['Title'], html.Span(user_data['Span'], style=dict(fontFamily='"Noah Regular", monospace', marginLeft=6, fontSize=18))],
                    id='ModalHead', style={'background-color': to_css_rgba(user_data['UserColor'])}
                ),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Имя", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserName', placeholder='Имя сотрудника', className='inp', value=user_data['UserName']),
                            dbc.Label("Логин", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserLogin', placeholder='Логин', className='inp', value=user_data['UserLogin']),
                            dbc.Label("Пароль", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserPass', placeholder='Пароль', className='inp', value=user_data['UserPass']),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Фото", style={'margin-bottom': 0, 'color': '#999'}),
                            html.Img(src=get_user_picture(user_data['UserLogin']), style={'height': '200px', 'border-radius': '6px'}),
                        ], width=6)
                    ], className="gx-5"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Роль"),
                            dcc.Tabs(
                                id='UserRole',
                                value='tab-admin' if user_data['UserRole'] else 'tab-user',
                                children=[
                                    dcc.Tab(label='Юзер', value='tab-user', className='custom-tab switch', selected_className='custom-tab--selected switch_selected'),
                                    dcc.Tab(label='Админ', value='tab-admin', className='custom-tab switch', selected_className='custom-tab--selected switch_selected')
                                ],
                                parent_className='role_switch',
                                className='custom-tabs-container'
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Цвет"),
                            dbc.Input(
                                type="color",
                                id="UserColor",
                                value=rgba_string_to_hex(user_data['UserColor']),
                                className='colorpicker'
                            )
                        ], width=6)
                    ], className="gx-5"),
                    dcc.Checklist(id='UserActual', className='check', options=[{'label': 'Актуальный', 'value': '1'}],
                                  value=f'{user_data["UserActual"]}', style={'width': '170px'})
                ], style={'paddingLeft': 16}),
                dbc.ModalFooter([
                    dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete",
                               style={'visibility': 'visible' if UPDATE_DICT else 'hidden'}),
                    dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit")
                ])
            ]
            return modal, Open

        elif tab == 'tab-p':
            today = date.today().strftime('%Y-%m-%d')
            if UPDATE_DICT:
                p = db.get_project_full(id)
                stages = db.get_project_stages(id)
                prj_data = dict(
                    Title=p[1],
                    Span=f'ID: {id}',
                    PrjName=p[1],
                    PrjSqr=p[2],
                    PrjLvl=p[3],
                    PrjStart=p[4],
                    PrjDone=p[5],
                    stages=stages
                )
            else:
                prj_data = dict(
                    Title='НОВЫЙ ПРОЕКТ',
                    Span='',
                    PrjName=None,
                    PrjSqr=None,
                    PrjStart=today,
                    PrjLvl=1,
                    PrjDone=0,
                    stages=[None] * 6
                )

            def generate_stage_rows(stages, today):
                stage_data = [
                    ("1. Подготовка", 'StageDate1', stages[0]),
                    ("2. 3D Графика", 'StageDate2', stages[1]),
                    ("3. Заказные позиции", 'StageDate3', stages[2]),
                    ("4. СМР", 'StageDate4', stages[3]),
                    ("5. Комплектация", 'StageDate5', stages[4]),
                    ("6. Реализация", 'StageDate6', stages[5]),
                ]

                rows = []
                for i in range(0, len(stage_data), 2):
                    row = dbc.Row([
                        dbc.Col([
                            html.Label(stage_data[i][0], className='d-table',
                                       style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.DatePickerSingle(
                                id=stage_data[i][1],
                                initial_visible_month=today,
                                display_format='YYYY-MM-DD',
                                placeholder='Дата дедлайна',
                                style={'text-align': 'left'},
                                date=stage_data[i][2]
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label(stage_data[i + 1][0], className='d-table',
                                       style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.DatePickerSingle(
                                id=stage_data[i + 1][1],
                                initial_visible_month=today,
                                display_format='YYYY-MM-DD',
                                placeholder='Дата дедлайна',
                                style={'text-align': 'left'},
                                date=stage_data[i + 1][2]
                            )
                        ], width=6)
                    ], className="gx-3", style={'margin-bottom': '8px' if i < 4 else '24px'})
                    rows.append(row)
                return rows

            modal = [
                dbc.ModalHeader([prj_data['Title'], html.Span(prj_data['Span'], style=dict(color='lightgray',
                                                                                           fontFamily='"Noah Regular", monospace',
                                                                                           marginLeft=6, fontSize=18))],
                                id='ModalHead'),
                dbc.ModalBody([
                    dbc.Row([dbc.Col([
                        dbc.Label("Название проекта", style={'margin-top': '12px'}),
                        dcc.Input(id='PrjName', placeholder='Введите название', className='inp long',
                                  value=prj_data['PrjName'])
                    ], width=6)]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Дата начала", style={'color': '#999'}),
                            dcc.Input(id='PrjStart', placeholder='Дата', className='inp', value=prj_data['PrjStart'])
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Площадь", style={'color': '#999'}),
                            dcc.Input(id='PrjSqr', placeholder='м²', className='inp short', value=prj_data['PrjSqr'])
                        ], width=6)
                    ]),
                    dbc.Label("Стадии проекта", style={'margin-top': '14px'}),
                    dbc.Row([dbc.Col(generate_stage_rows(prj_data['stages'], today))]),
                    dbc.Label("Уровень важности"),
                    dcc.Slider(id="PrjLvl", min=1, max=5, step=1, value=prj_data['PrjLvl'],
                               marks={i: str(i) for i in range(1, 6)}),
                    dcc.Checklist(id='PrjActual', className='check',
                                  options=[{'label': 'Закончен', 'value': '1'}],
                                  value=f'{prj_data["PrjDone"]}')
                ], style={'paddingLeft': 16}),
                dbc.ModalFooter([
                    dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete",
                               style={'visibility': 'visible' if UPDATE_DICT else 'hidden'}),
                    dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit")
                ])
            ]

            return modal, Open

        raise PreventUpdate

    except Exception as e:
        logger.exception("Ошибка в RenderModal: %s", str(e))
        return dash.no_update, False


@appDash.callback(
    Output('ModalDelete', 'style'),
    [Input('PrjName', 'value')],
    [Input('PrjStart', 'value')],
    [Input('PrjSqr', 'value')],
    [Input('PrjLvl', 'value')],
    [Input('PrjActual', 'value')],
    [Input('StageDate1', 'date')],
    [Input('StageDate2', 'date')],
    [Input('StageDate3', 'date')],
    [Input('StageDate4', 'date')],
    [Input('StageDate5', 'date')],
    [Input('StageDate6', 'date')],
    prevent_initial_call=True
)
def ProjectChanges(PrjName, PrjStart, PrjSqr, PrjLvl, PrjDone,
                StageDate1, StageDate2, StageDate3, StageDate4, StageDate5, StageDate6):
    try:
        changed_id = dash.callback_context.triggered[0]['prop_id']
        info_fields = {
            'PrjName': PrjName,
            'PrjStart': PrjStart,
            'PrjSqr': PrjSqr,
            'PrjLvl': PrjLvl,
        }

        for key, value in info_fields.items():
            if key in changed_id:
                CACHE[key] = f"'{value}'"
                CACHE['info'] = True
                break

        if 'PrjActual' in changed_id:
            CACHE['PrjDone'] = 1 if '1' in PrjDone else 0
            CACHE['info'] = True

        for i in range(1, 7):
            stage_key = f'StageDate{i}'
            if stage_key in changed_id:
                date_value = locals()[stage_key]
                CACHE[stage_key] = f"'{date_value}'"
                CACHE['stages'] = True
                break
        return dash.no_update

    except Exception as e:
        logger.exception("Ошибка в ProjectChanges: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('popupAdm', 'style'),
    [Input('UserName', 'value')],
    [Input('UserLogin', 'value')],
    [Input('UserPass', 'value')],
    [Input('UserRole', 'value')],
    [Input('UserActual', 'value')],
    [Input('UserColor', 'value')],
    prevent_initial_call=True
)
def UserChanges(UserName, UserLogin, UserPass, UserRole, UserActual, UserColor):
    try:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if 'UserName' in changed_id:
            CACHE['UserName'] = f"{UserName}"
        elif 'UserLogin' in changed_id:
            CACHE['UserLogin'] = f"{UserLogin}"
        elif 'UserPass' in changed_id:
            CACHE['UserPass'] = f"{UserPass}"
        elif 'UserRole' in changed_id:
            CACHE['UserRole'] = UserRole
        elif 'UserColor' in changed_id:
            CACHE['UserColor'] = hex_to_rgba01(UserColor)
        elif 'UserActual' in changed_id:
            CACHE['UserActual'] = 1 if '1' in UserActual else 0
        return dash.no_update
    except Exception as e:
        logger.exception("Ошибка в UserChanges: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('popupAdm', 'children'),
    [Input('ModalSubmit', 'n_clicks'),
     Input('ConfirmDelete', 'submit_n_clicks')],
    [State('popupAdm', 'children'),
     State('ModalHead', 'children'),
     State("tabs", "value")],
    prevent_initial_call=True
)
def UpdateDict(n_clicks1, n_clicks2, old, head, tab):

    triggered = dash.callback_context.triggered
    if not triggered or triggered[0]['value'] is None:
        return dash.no_update

    if not n_clicks1 and not n_clicks2:
        return dash.no_update

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'ModalSubmit' in changed_id and ('новый юзер' in head[0].lower() or 'новый проект' in head[0].lower()):
        mode = 'insert'
    elif 'ConfirmDelete' in changed_id:
        mode = 'delete'
    elif 'ModalSubmit' in changed_id:
        mode = 'update'
    else:
        return dash.no_update

    item_id = CACHE.pop('id', None)

    try:
        if tab == 'tab-c':
            db.execute_user_queries(CACHE, item_id, mode)
        elif tab == 'tab-p':
            db.execute_project_queries(CACHE, item_id, mode)
        else:
            raise ValueError(f"Неизвестная вкладка: {tab}")
    except Exception as e:
        logger.exception(f"Ошибка при выполнении SQL: {e}")
        CACHE.clear()
        return old + [html.Div(["😧 Ошибка при записи в базу"], className='cloud line popup orange', hidden=False)]

    CACHE.clear()

    msg = {
        'insert': "✔ Данные добавлены!",
        'update': "✔ Данные обновлены!",
        'delete': "✂️ Успешно удалено!"
    }[mode]
    print(msg)

    return old + [html.Div([msg], className='cloud line popup green', hidden=False)]


@appDash.callback(
    Output('popupBoxAdm', 'children'),
    Input('popupAdm', 'children'),
    prevent_initial_call=True
)
def SaveAdm(ch):
    # print(ch)
    if len(ch) != 0:
        sleep(2.5)
        return html.Div([], id='popupAdm', className='line')
    else:
        dash.no_update()

