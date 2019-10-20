
import numpy as np
import pandas.io.sql as psql
import sqlite3 as sql

from bokeh.plotting import figure
from bokeh.layouts import layout, column, row
from bokeh.models import ColumnDataSource, Div, HoverTool, Label
from bokeh.models.widgets import Slider, Select, TextInput, Toggle
from bokeh.io import curdoc
from bokeh.sampledata.movies_data import movie_path


def get_table(psql, conn, player_name):
    return psql.read_sql("SELECT * FROM {0}".format(player_name), conn)

conn = sql.connect("test_table.db")
crsr = conn.cursor() 


tables = crsr.execute('SELECT name from sqlite_master where type= "table"')
tables = [x[0] for x in tables.fetchall()]




source_1 = ColumnDataSource(data=dict(x=[], y=[], date=[], bf=[], runs=[], opposition=[], sr=[], name=[]))
source_2 = ColumnDataSource(data=dict(x=[], y=[], date=[], bf=[], runs=[], opposition=[], sr=[], name=[]))
# source = ColumnDataSource(table)

# source.data = dict(x=table.index, y=table["Runs"], sr=table["SR"], bf=table["BF"],
#                    date=table["Start_Date"], opposition=table["Opposition"],
#                    runs=table["Runs"])

# Set up plot
TOOLTIPS= [
    ("Name", "@name"),
    ("Date", "@date"),
    ("Opposition", "@opposition"),
    ("Runs", "@runs"),
    ("BF", "@bf"),
    ("SR", "@sr"),

]
plot = figure(plot_height=800, plot_width=1000, title="Player comparison",
               sizing_mode="scale_both", tooltips=TOOLTIPS)
axis_map = {
    "SR": "SR",
    "Runs": "Runs",
    "Match": "Start_Date",
    "BF": "BF",
}


fraction = 100
balls_faced = Slider(title="Balls faced", value=0, start=0, end=300, step=1)
strike_rate = Slider(title="Strike Rate", value=0, start=0, end=600, step=1)
runs = Slider(title="Runs", value=0, start=0, end=320, step=1)
label_1 = Label(x=70, y=70, x_units='screen', text='100 %% of innings'.format(fraction))
plot.add_layout(label_1)
x_axis = Select(title="X Axis", options=sorted(axis_map.keys()), value="BF")
y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Runs")
player_1 = Select(title="Player 1", options=sorted(tables), value="chris_woakes")
player_2 = Select(title="Player 2", options=sorted(tables), value="eoin_morgan")

plot.circle(x="x", y="y", source=source_1, size=7, line_color=None, alpha=0.75)
plot.circle(x="x", y="y", source=source_2, size=7, line_color=None, alpha=0.75, color="Orange")

table_1 = get_table(psql, conn, player_1.value)
table_2 = get_table(psql, conn, player_2.value)

def select_innings(table_1, table_2):
    selected_1 = table_1[(table_1.BF >= balls_faced.value) &
                        (table_1.SR >= strike_rate.value) &
                        (table_1.Runs >= runs.value)]
    selected_2 = table_2[(table_2.BF >= balls_faced.value) &
                        (table_2.SR >= strike_rate.value) &
                        (table_2.Runs >= runs.value)]

    return selected_1, selected_2

def update():
    table_1 = get_table(psql, conn, player_1.value)
    table_2 = get_table(psql, conn, player_2.value)

    selected_1, selected_2 = select_innings(table_1, table_2)
    # print(len(selected_2), len(table_2))
    fraction = (len(selected_2)/len(table_2))*100
    label_1.text = "{0}: {1:.1f} % of innings".format(player_2.value, fraction)
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    plot.xaxis.axis_label = x_axis.value
    plot.yaxis.axis_label = y_axis.value

    source_1.data = dict(
        x=selected_1[x_name],
        y=selected_1[y_name],
        sr=selected_1["SR"],
        bf=selected_1["BF"],
        date=selected_1["Start_Date"],
        opposition=selected_1["Opposition"],
        runs=selected_1["Runs"],
        name=[player_1.value for x in range(len(selected_1))]
    )
    source_2.data = dict(
        x=selected_2[x_name],
        y=selected_2[y_name],
        sr=selected_2["SR"],
        bf=selected_2["BF"],
        date=selected_2["Start_Date"],
        opposition=selected_2["Opposition"],
        runs=selected_2["Runs"],
        name=[player_2.value for x in range(len(selected_2))]
    )

    
controls = [balls_faced, strike_rate, runs, x_axis, y_axis, player_1, player_2]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())


inputs = column(controls)
# inputs.sizing_mode = "fixed"
# l = layout([inputs, plot], sizing_mode="scale_both")
# Set up layouts and add to document
# inputs = column(text, offset, amplitude, phase, freq)
update()
curdoc().add_root(row(inputs, plot, width=1000))
# curdoc().add_root(plot)
# curdoc().title = "Sliders"