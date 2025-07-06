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

# @cache.memoize()
# @appDash.callback(
#     Output('TableDB', 'data'),
#     Output('TableDB', 'columns'),
#     Output('RowCount', 'children'),
#     Output('MonthFilter', 'disabled'),
#     Output('DayFilter', 'disabled'),
#     Output('MonthFilter', 'options'),
#     Output('DayFilter', 'options'),
#     Input('UserFilter', 'value'),
#     Input('ProjectFilter', 'value'),
#     Input('CustomerFilter', 'value'),
#     Input('DayFilter', 'value'),
#     Input('MonthFilter', 'value'),
#     Input('YearFilter', 'value'),
#     prevent_initial_call=True
# )
# def update_db(user, project, customer, day, month, year):
#     con = engine.connect()
#     df=dbDF[0]
#     groupby = []
#     monthD = True
#     dayD = True
#
#     if year is not None:
#         groupby.append('ГОД')
#         monthD = False
#         if year != 'Все':
#             df = df[(df['ГОД'] == year)]
#     monthOp = [{'label': i, 'value': i} for i in df['ММ'].unique()] + [{'label': '✱', 'value': 'Все'}]
#     if month is not None:
#         groupby.append('ММ')
#         dayD = False
#         if month != 'Все':
#             df = df[(df['ММ'] == month)]
#     dayOp = [{'label': i, 'value': i} for i in df['ДД'].unique()] + [{'label': '✱', 'value': 'Все'}]
#     if day is not None:
#         groupby.append('ДД')
#         if day != 'Все':
#             df = df[(df['ДД'] == day)]
#
#     if user is not None:
#         groupby.append('СОТРУДНИК')
#         if user != 'Все':
#             df = df[(df['СОТРУДНИК'] == user)]
#
#     if project is not None:
#         if 'ПРОЕКТ' not in groupby:
#             groupby.append('ПРОЕКТ')
#         if 'ШИФР' not in groupby:
#             groupby.append('ШИФР')
#         if 'ЗАКАЗЧИК' not in groupby:
#             groupby.append('ЗАКАЗЧИК')
#         if project != 'Все':
#             df = df[(df['ПРОЕКТ'] == project)]
#
#     if customer is not None:
#         # if 'ПРОЕКТ' not in groupby:
#         #     groupby.append('ПРОЕКТ')
#         # if 'ШИФР' not in groupby:
#         #     groupby.append('ШИФР')
#         if 'ЗАКАЗЧИК' not in groupby:
#             groupby.append('ЗАКАЗЧИК')
#         if customer != 'Все':
#             df = df[(df['ЗАКАЗЧИК'] == customer)]
#
#     if len(groupby) != 0:
#         df = df.groupby(groupby)['ЧАСЫ'].sum().reset_index()
#     try:
#         df = df.sort_values('ГОД', ascending=False)
#     except:
#         pass
#
#     cols = [{"name": i, "id": i} for i in df.columns]
#     if df.shape[0] == 0:
#         cols = [{"name": '⦰  ПУСТОЕ МНОЖЕСТВО', "id": 0}]
#     return df.to_dict('records'), cols, [df.shape[0],
#                                          html.Span('кол. строк', className='tail')], monthD, dayD, monthOp, dayOp
#
#
# @appDash.callback(
#     Output('UserFilter', 'value'),
#     Output('ProjectFilter', 'value'),
#     Output('CustomerFilter', 'value'),
#     Output('DayFilter', 'value'),
#     Output('MonthFilter', 'value'),
#     Output('YearFilter', 'value'),
#     Input('refresh', 'n_clicks'),
#     prevent_initial_call=True
# )
# def cleanFilter(n_clicks):
#     return None, None, None, None, None, None
#
#
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
#
@appDash.callback(
    Output('ConfirmDelete', 'displayed'),
    Output('ConfirmDelete', 'message'),
    [Input('ModalSubmit', 'n_clicks'), Input('ModalDelete', 'n_clicks')],
    State("tabs", "value"),
    prevent_initial_call=True
)
def ShowConfirm(clickS, clickD, tab):
    triggered = dash.callback_context.triggered
    if not triggered or triggered[0]['value'] is None:
        return dash.no_update, dash.no_update

    changed_id = triggered[0]['prop_id']
    message = f'Внимание! При удалении {"проекта" if tab =="tab-p" else "юзера"}' \
                           f' также навсегда удалятся все связанные с ним записи!'

    if 'ModalSubmit' in changed_id:
        return False, dash.no_update
    elif 'ModalDelete' in changed_id:
        return True, message

    return dash.no_update,dash.no_update



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

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'EditButton' in changed_id:
        UPDATE_DICT = True
        Open = True
    elif 'AddButton' in changed_id:
        UPDATE_DICT = False
        Open = True
    elif 'ModalSubmit' in changed_id:
        return dash.no_update, False
    elif 'ModalDelete' in changed_id:
        return dash.no_update, False
    else:
        UPDATE_DICT = False
        Open = False

    CACHE.clear()

    if row is not None and len(row) != 0 : id = row[0]
    else: id = None
    CACHE['id'] = id

    if tab == 'tab-c':
        if UPDATE_DICT:
            row = db.get_user_full(id)
            # print(row)
            Span = 'ID: '+str(id)
            UserName = row[1]
            UserLogin = row[2]
            UserRole = row[3]
            UserActual = row[4]
            UserColor = row[5]
            UserPass = row[6]
            Title = UserName.upper()
        else:
            Title = 'Новый Юзер'.upper()
            Span = ''
            UserName, UserLogin, UserPass, UserRole, UserActual, UserColor = None,None,None,0,1,'0.3,0.3,0.3,1'

        return \
        [
            dbc.ModalHeader([Title,
                             html.Span(Span,style=dict(fontFamily='"Noah Regular", monospace',marginLeft=6,fontSize=18))],id='ModalHead',
                            style={'background-color':to_css_rgba(UserColor)}),
            dbc.ModalBody(
                [
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Имя", html_for="input", style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.Input(id='UserName', placeholder='Имя сотрудника', className='inp', value=UserName),
                            dbc.Label("Логин", html_for="input", style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.Input(id='UserLogin', placeholder='Логин', className='inp', value=UserLogin),
                            dbc.Label("Пароль", html_for="input", style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.Input(id='UserPass', placeholder='Пароль', className='inp', value=UserPass),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Фото", html_for="img", style={'margin-bottom': '0', 'color': '#999999'}),
                            html.Img(src=get_user_picture(UserLogin), style={'height':'200px', 'border-radius':'6px',})

                        ], width=6),
                    ], className="gx-5"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Роль", html_for="UserRole"),
                            # dcc.Slider(id="UserRole", min=0, max=1, step=1, value=UserRole,
                            #            marks={0: 'Юзер', 1: 'Админ'}, ),
                            dcc.Tabs(id='UserRole', value='tab-user' if UserRole==0 else 'tab-admin', children=[
                                dcc.Tab(label='Юзер', value='tab-user', className='custom-tab switch',
                                        selected_className='custom-tab--selected switch_selected'),
                                dcc.Tab(label='Админ', value='tab-admin', className='custom-tab switch',
                                        selected_className='custom-tab--selected switch_selected'),
                            ], parent_className='role_switch', className='custom-tabs-container', ),
                        ], width=6, style={'padding-right':'0'}),
                        dbc.Col([
                            dbc.Row(
                                [
                                    dbc.Col([
                                        dbc.Label("Цвет", html_for="UserColor"),
                                        dbc.Input(
                                            type="color",
                                            id="UserColor",
                                            name="head",
                                            value=rgba_string_to_hex(UserColor),
                                            className='colorpicker'
                                        )

                                    ])
                                ],
                            )
                        ], width=6)
                    ], className="gx-5"),



                    dcc.Checklist(id='UserActual',className='check',options=[{'label': 'Актуальный', 'value': '1'},],value=f'{UserActual}', style={'width':'170px'})
                ], style=dict(paddingLeft=16)
            ),
            dbc.ModalFooter([
                dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete", style=dict(visibility='hidden' if not UPDATE_DICT else 'visible') ),
                dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit", )]
            ),
        ], Open
    elif tab == 'tab-p':
        stage_marks = {1: '1', 2: '2', 3:'3', 4:'4', 5:'5'}
        if UPDATE_DICT:
            row = db.get_project_full(id)
            Span = 'ID: ' + str(id)
            PrjName = row[1]
            PrjSqr = row[2]
            PrjLvl = row[3]
            PrjStart = row[4]
            PrjDone = row[5]
            Title = PrjName
            today = date.today().strftime('%Y-%m-%d')
            stages = db.get_project_stages(id)
        else:
            Title = 'Новый Проект'.upper()
            Span = ''
            today = date.today().strftime('%Y-%m-%d')
            PrjName, PrjSqr, PrjStart,PrjLvl, PrjDone = None,None,today,1,0
            stages = [None] * 6

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

        return \
            [
                dbc.ModalHeader([Title, html.Span(Span, style=dict(color='lightgray',fontFamily='"Noah Regular", monospace',marginLeft=6,fontSize=18))],id='ModalHead'),
                dbc.ModalBody(
                    [
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Название проекта", style={'margin-top':'12px',}),
                                dcc.Input(id='PrjName', placeholder='Введите название', className='inp long', value=PrjName),
                            ], width=6),

                        ], className="gx-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Дата начала", html_for="input",
                                          style={'margin-bottom': '0', 'color': '#999999'}),
                                dcc.Input(id='PrjStart', placeholder='Заказчик', className='inp', value=PrjStart),
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Площадь", html_for="PrjSqr",
                                          style={'margin-bottom': '0', 'color': '#999999'}),
                                dcc.Input(id='PrjSqr', placeholder='м²', className='inp short', value=PrjSqr),
                            ], width=6),
                        ], className="gx-3"),


                        dbc.Label("Стадии проекта", style={'margin-top':'14px',}),
                        dbc.Row([dbc.Col(generate_stage_rows(stages, today))]),

                        dbc.Label("Уровень важности", html_for="slider"),
                        dcc.Slider(id="PrjLvl", min=1, max=5, step=1, value=PrjLvl, marks=stage_marks),

                        dcc.Checklist(id='PrjActual', className='check',
                                      options=[{'label': 'Закончен', 'value': '1'}, ], value=f'{PrjDone}')
                    ], style=dict(paddingLeft=16)
                ),
                dbc.ModalFooter([
                    dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete",
                               style=dict(visibility='hidden' if not UPDATE_DICT else 'visible')),
                    dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit")]
                ),
            ], Open

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
def UserChanges(PrjName, PrjStart, PrjSqr, PrjLvl, PrjDone,
                StageDate1, StageDate2, StageDate3, StageDate4, StageDate5, StageDate6):

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
    # if item_id is None:
    #     logger.error("CACHE не содержит 'id'")
    #     return old + [html.Div(["Ошибка: не найден ID элемента."], className='cloud line popup orange', hidden=False)]

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

