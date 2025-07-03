from app import engine
from sqlalchemy import text
import pandas as pd


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
        df = pd.read_sql("SELECT id, name, admin, relevant  FROM lptv.user", con)
        return df

def get_projects():
    with engine.connect() as con:
        df = pd.read_sql("SELECT id, name, square, startdate, relevant  FROM lptv.project", con)
        return df

def get_projects(relevant, year):
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



