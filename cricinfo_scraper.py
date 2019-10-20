import sqlite3
import urllib.error as errors
from urllib.request import urlopen

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


def get_tables(cricinfo_id):
    """Returns all of the tables in a page for a given player id
    Args:
        - cricinfo_id: the player id
    Return:
        - tables:  bs4.element.ResultSet
        """
    
    url = f"http://stats.espncricinfo.com/ci/engine/player/{cricinfo_id}.html?class=2;template=results;type=batting;view=innings"
    try:
        html = urlopen(url)
        soup = BeautifulSoup(html, 'lxml')
        tables = soup.find_all("table")
        return tables

    except errors.HTTPError as err:
        print(err)
        return None
    

def get_name(cricinfo_id, no_space=False):
    """Returns the name of a player given some id 
    Args:
        - cricinfo_id: the player id
        - no_space: bool for whether to return the name with spaces
    Return:
        - name: name of player as a str
        """
    
    url = f"http://www.espncricinfo.com/england/content/player/{cricinfo_id}.html"
    try:
        html = urlopen(url)
    except errors.HTTPError:
        return "NULL"

    soup = BeautifulSoup(html, 'lxml')
    name  = soup.find_all("title")[0].text.split("-")[0].strip()

    if "'" in name:
        name = name.replace("'", "")

    if no_space:
        return name.replace(" ", "_").lower()
    else:
        return name


def get_column_names(tables):
    """Returns list of column names from the web page"""

    column_names = []
    for column in tables[3].find_all("tr")[0].find_all("th"):
        column_names.append(column.text)
    return column_names


def str_to_float(row_dict):
    for col in ["Mins", "BF", "4s", "6s", "SR", "Pos", "Inns"]:
        if row_dict[col] == "-":
            row_dict[col] = -1
        row_dict[col] = float(row_dict[col])
    return row_dict


def create_dataframe(column_names, tables):
    """Creates a pandas dataframe from webpage tables.
    Args:
        - column_names: List of the column names
        - tables: tables of the webpage
    Reutrns:
        - df: pandas dataframe
    """

    vals = []
    for i,row in enumerate(tables[3].find_all("tr")[1:]):
        row_dict = {col_name: 0 for col_name in column_names}
        for j,col in enumerate(row.find_all("td")):
            row_dict[column_names[j]] = col.text
        if not row_dict["Runs"] == "DNB" and not row_dict["Runs"] == "TDNB" and not row_dict["Runs"] == "sub":
            if "*" in row_dict["Runs"]:
                row_dict["Notout"] = 1
                row_dict["Runs"] = float(row_dict["Runs"].replace("*",""))
            else:
                row_dict["Notout"] = 0
                row_dict["Runs"] = float(row_dict["Runs"])
            
            row_dict = str_to_float(row_dict)
            row_dict["Inns"] = int(row_dict["Inns"])
            vals.append(row_dict)

    df = pd.DataFrame(vals)

    return df


def get_database_connection(table_path):
    connection = sqlite3.connect(table_path)
    return connection


def create_player_table(cursor, table_name, df):
    type_map = {np.float64: "FLOAT", 
               np.int64: "INT",
               str: "VARCHAR(255)"}
    sql_command = f"CREATE TABLE IF NOT EXISTS {table_name} (".format(table_name)
    for i,col in enumerate(df.columns[1:]):
        col = col.replace(" ", "_")
        col_type = type_map[type(df[col][0])]
        sql_command += f"'{col}' {col_type}"
        if i != len(df.columns[1:])-1:
            sql_command += ", "
    sql_command += ");"

    cursor.execute(sql_command)
    

def insert_player_data(cursor, table_name, df):
    for index,row in df.iterrows():
        sql_command = f"INSERT INTO {table_name} VALUES ("
        for i,col in enumerate(df.columns[1:]):
            if type(row[col]) == str:
                sql_command += f'"{row[col]}"'
            else:
                sql_command += f"{row[col]}"
            if i != len(df.columns[1:])-1:
                sql_command += ", "
        sql_command += ");"

        cursor.execute(sql_command) 


def fill_table(connection, cricinfo_id):
    cursor = connection.cursor()
    tables = get_tables(cricinfo_id=cricinfo_id)
    if tables:
        print(cricinfo_id,get_name(cricinfo_id=cricinfo_id, no_space=True))
        column_names= get_column_names(tables=tables)
        print(column_names)
        if len(column_names) == 0:
            print("No ODI data!")
            return None
        df = create_dataframe(column_names=column_names, tables=tables)
        if len(df) == 0:
            print("Didnt bat")
            return None
        create_player_table(cursor=cursor, table_name=get_name(cricinfo_id=cricinfo_id, no_space=True), df=df)
        insert_player_data(cursor=cursor, table_name=get_name(cricinfo_id=cricinfo_id, no_space=True), df=df)
        
        connection.commit()


"""Only for england players at the moment. Need to make a more general function"""
def get_player_ids():
    url = "http://www.espncricinfo.com/england/content/player/caps.html?country=1;class=2"
    html = urlopen(url)
    soup = BeautifulSoup(html, 'lxml')
    player_ids = []

    for a in range(1,255):
        tables = soup.find_all("div")[17].find_all("ul")[a].find_all("li")[1].find_all("a")[0]
        player_ids.append(int(tables.get("href").split("/")[-1].split(".")[0]))
    return player_ids
    

if __name__ == "__main__":
    connection  = get_database_connection("england_stats.db")
    player_ids = get_player_ids()

    for player in player_ids:
        fill_table(connection=connection, cricinfo_id=player)

