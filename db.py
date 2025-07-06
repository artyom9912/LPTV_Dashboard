from app import engine
from sqlalchemy import text
import pandas as pd
from datetime import date
import os

def execute_query(con, query: str):
    if query:
        res= con.execute(text(query))
        con.commit()
        return res

def get_user_info(user_id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, username, relevant, admin, name, color FROM lptv.user WHERE id = :user_id'),
            {"user_id": user_id}
        )
        return res.fetchone()


def get_user(username):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, password FROM lptv.user WHERE relevant = 1 AND username LIKE :username'),
            {"username": username}
        )
        return res.fetchone()

def get_user_login(name):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT username FROM lptv.user WHERE relevant = 1 AND name LIKE :name'),
            {"name": name}
        )
        return res.scalar()

def get_user_login_by_id(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT username FROM lptv.user WHERE id = :id'),
            {"id": id}
        )
        return res.scalar()

def get_user_full(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, name, username, admin, relevant, color, password FROM lptv.user WHERE id = :id'),
            {"id": id}
        )
        return res.fetchone()

def get_project_full(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, name, square, level, startdate, isDone FROM lptv.project WHERE id = :id'),
            {"id": id}
        )
        return res.fetchone()

def get_project_count(is_relevant=1):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT count(*) AS rel FROM lptv.project WHERE isDone != :is_relevant'),
            {"is_relevant": is_relevant}
        )
        return res.scalar()


def get_years():
    with engine.connect() as con:
        res = con.execute(
            text('SELECT DISTINCT YEAR(dateStamp) AS year FROM lptv.main ORDER BY year DESC')
        )
        return [str(row[0]) for row in res]

def get_users():
    with engine.connect() as con:
        df = pd.read_sql("SELECT id, name, color, admin, relevant  FROM lptv.user", con)
        return df

def get_projects():
    with engine.connect() as con:
        df = pd.read_sql("SELECT id, name, square, startdate, isDone "
                         "FROM lptv.project ORDER BY id DESC", con)
        return df

def get_project_stages(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT finishdate FROM lptv.projectstage '
                 'WHERE projectId = :id ORDER BY stageId'),
            {"id": id}
        )
        return [str(row[0]) for row in res]

def get_project_cards(relevant, year):
    base_query = text("""
        SELECT name, square, count_users, sum_hours, isDone, level
        FROM lptv.project p
        LEFT JOIN (
            SELECT projectId, count(distinct userId) count_users, sum(hours) sum_hours, max(dateStamp) lastAct
            FROM lptv.main
            GROUP BY projectId
        ) as agr ON (projectId = p.id)
        WHERE 1=1
        {relevant_filter}
        {year_filter}
        ORDER BY isDone, p.level DESC, lastAct DESC
    """)

    # фильтры
    filters = {
        "relevant_filter": "",
        "year_filter": ""
    }
    params = {}

    if relevant == 'Архивные':
        filters["relevant_filter"] = " AND p.isDone != :relevant_val"
        params["relevant_val"] = 0
    elif relevant == 'Актуальные':
        filters["relevant_filter"] = " AND p.isDone != :relevant_val"
        params["relevant_val"] = 1

    if year is not None and year != 'Всё время':
        filters["year_filter"] = """
            AND p.id IN (
                SELECT DISTINCT projectId
                FROM lptv.main
                WHERE YEAR(dateStamp) = :year_val
            )
        """
        params["year_val"] = int(year)

    # Подставляем текст фильтров
    final_query = text(
        base_query.text.format(
            relevant_filter=filters["relevant_filter"],
            year_filter=filters["year_filter"]
        )
    )

    with engine.connect() as con:
        df = pd.read_sql(final_query, con=con, params=params)

    return df

def execute_user_queries(cache, user_id, mode):
    MAP = {
        'UserName': 'name',
        'UserLogin': 'username',
        'UserPass': 'password',
        'UserRole': 'admin',
        'UserActual': 'relevant',
        'UserColor': 'color'
    }

    def fmt(value):
        return f"'{value}'" if isinstance(value, str) and not value.startswith("'") else str(value)

    with engine.connect() as con:
        if mode == 'update':
            updates = [
                f"{MAP[k]} = {fmt(cache[k])}"
                for k in cache if k in MAP
            ]
            if updates:
                if 'UserLogin' in cache.keys():
                    path = 'assets/img/users/'
                    old_name = get_user_login_by_id(user_id)
                    print(old_name)
                    if os.path.isfile(path+old_name+'.png'):
                        os.rename(path+old_name+'.png', path+cache['UserLogin']+'.png')

                sql = f"UPDATE lptv.user SET {', '.join(updates)} WHERE id = {user_id}"
                execute_query(con, sql)

        elif mode == 'insert':
            cache.setdefault('UserRole', 0)
            cache.setdefault('UserActual', 1)
            cache.setdefault('UserColor', '0.5,0.5,0.5,1')

            fields = [MAP[k] for k in MAP]
            values = [fmt(cache.get(k)) for k in MAP]

            sql = f"""INSERT INTO lptv.user 
                      ({', '.join(fields)}) 
                      VALUES ({', '.join(values)})"""
            execute_query(con, sql)

        elif mode == 'delete':
            sql1 = f"DELETE FROM lptv.main WHERE userId = {user_id}"
            sql2 = f"DELETE FROM lptv.user WHERE id = {user_id}"
            execute_query(con, sql1)
            execute_query(con, sql2)



def execute_project_queries(cache, project_id, mode):
    with engine.connect() as con:
        MAP = {
            'PrjName': 'name',
            'PrjStart': 'startdate',
            'PrjSqr': 'square',
            'PrjLvl': 'level',
            'PrjDone': 'isDone',
        }
        print(mode)
        print(cache)
        def fmt(value):
            return f"'{value}'" if isinstance(value, str) and not value.startswith("'") else str(value)


        if mode == 'update':
            cache.setdefault('info', 0)
            cache.setdefault('stages', 0)
            if cache['info']:
                fields = ', '.join(
                    f"{MAP[k]} = {fmt(cache[k])}" for k in cache if k in MAP
                )
                sql = f"UPDATE lptv.project SET {fields} WHERE id = {project_id}"
                execute_query(con, sql)
            if cache['stages']:
                for k in cache:
                    if k.startswith('StageDate'):
                        stage_id = k[-1]
                        sql = f"""UPDATE lptv.projectstage
                                             SET finishdate = {fmt(cache[k])}
                                             WHERE projectId = {project_id} AND stageId = {stage_id}"""
                        execute_query(con, sql)


        elif mode == 'insert':
            cache.setdefault('PrjDone', 0)
            cache.setdefault('PrjLvl', 1)
            cache.setdefault('PrjStart', f"'{date.today().strftime('%Y-%m-%d')}'")

            columns = ', '.join(MAP.values())
            values = ', '.join(fmt(cache.get(k, 'NULL')) for k in MAP)

            sql = f"INSERT INTO lptv.project ({columns}) VALUES ({values})"
            res = execute_query(con, sql)
            last_id = res.lastrowid

            for stage in range(1, 7):
                key = f"StageDate{stage}"
                if key in cache:
                    sql = f"""INSERT INTO lptv.projectstage (projectId, stageId, finishdate)
                                          VALUES ({last_id}, {stage}, {fmt(cache[key])})"""
                    execute_query(con, sql)

        elif mode == 'delete':
            sql = f"DELETE FROM lptv.main WHERE projectId = {project_id}"
            sql2 = f"DELETE FROM lptv.projectstage WHERE projectId = {project_id}"
            sql3 = f"DELETE FROM lptv.project WHERE id = {project_id}"
            execute_query(con,sql)
            execute_query(con,sql2)
            execute_query(con,sql3)



