from flask import Flask, render_template, url_for, redirect,request
import datetime as dt
import pyodbc
import pandas as pd 
import plotly
from plotly.offline import download_plotlyjs, init_notebook_mode, iplot
from plotly.graph_objs import *
import plotly.plotly as py
import plotly.graph_objs as go
#init_notebook_mode()


app = Flask(__name__)
# Create the connection
server = 'ACER'
db = 'fin'
cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + db + ';Trusted_Connection=yes')
# query db
app.debug = True


@app.route('/')
def homepage():
	
	paragraph = ["Manage your incomes and expenses","Visualize the data with interactive charts"]
	return render_template("index.html", paragraph = paragraph)

@app.route('/list',methods=["GET", "POST" ])
def list():
	title = "List of incomes and expenses"
	paragraph = ["incomes and expenses"]
	
	#connect to the database
	cursor = cnxn.cursor()

	if request.method == "POST":
		#get info
		startdate = request.form.get('startdate')
		enddate = request.form.get('enddate')
		name = request.form.get("name")


		#get rows
		if name == "":  
			#rows = cursor.execute("""SELECT * FROM items WHERE itemdate >= ? and itemdate <= ? and itemtype = ? and name = ?""",startdate, enddate, itemtype, name).fetchall()
		#rows = cursor.execute("""SELECT * FROM items WHERE name = ? AND itemtype = ? ORDER BY itemdate DESC """, name, itemtype).fetchall()
			rows = cursor.execute("""SELECT * FROM items WHERE itemdate >= ? and itemdate <= ? """,startdate, enddate).fetchall()
		elif name !="":
			rows = cursor.execute("""SELECT * FROM items WHERE itemdate >= ? and itemdate <= ?  and name = ?  ORDER BY itemdate DESC """, startdate, enddate, name).fetchall()
		
		return render_template("list.html",title = title, rows = rows)

	else:
		rows = cursor.execute("""SELECT * FROM items ORDER BY itemdate DESC """).fetchall()
		return render_template("list.html", title = title, rows = rows)
	cnxn.commit() 
	cnxn.close()
	

@app.route('/pie')
def pie():
	title_ex = "Expenses"
	title_in ="Incomes"
	color_list = ["rgb(255, 139, 0)", "rgb(1, 249, 0)", "rgb(253, 253, 0)","rgb(253, 3, 153)","rgb(51, 204, 51)","rgb(51, 102, 255)","rgb(153, 153, 102)"]
	#make expense pie chart
	labellist_expense=[]
	valuelist_expense = []
	
	#query the database
	cursor = cnxn.cursor()
	sql_expense="""SELECT name as name_of_expenses , sum(amount)as expense_amounts FROM [fin].[dbo].[items]where itemtype ='expense' group by name"""
	df_expense = pd.read_sql(sql_expense, cnxn)
	labellist_expense= df_expense['name_of_expenses'].tolist()
	valuelist_expense = df_expense['expense_amounts'].tolist()

	trace_ex=go.Pie(labels=labellist_expense,values=valuelist_expense)

	piechart_ex = plotly.offline.plot([trace_ex], output_type="div", show_link=False, link_text=False)
	#make income pie chart
	labellist_income = []
	valuelist_income = []
	sql_income="""SELECT name as name_of_incomes , sum(amount)as income_amounts FROM [fin].[dbo].[items]where itemtype ='income' group by name"""
	df_income = pd.read_sql(sql_income, cnxn)
	labellist_income= df_income['name_of_incomes'].tolist()
	valuelist_income = df_income['income_amounts'].tolist()
	
	trace_in=go.Pie(labels=labellist_income,values=valuelist_income)

	piechart_in = plotly.offline.plot([trace_in], output_type="div", show_link=False, link_text=False)

	
	return render_template("pie.html",  piechart_ex=piechart_ex, piechart_in = piechart_in, title_in = title_in, title_ex  = title_ex )
	cnxn.commit()
	cnxn.close()
@app.route('/add', methods=["GET", "POST"])
def add():
	title = "Add incomes or expenses"
	if request.method == "POST":
		#get info
		itemdate = request.form.get("itemdate")
		itemtype = request.form.get("itemtype")
		name = request.form.get("name")
		amount = float(request.form.get("amount"))
		#connect to the database
		cursor = cnxn.cursor()
		cursor.execute("""INSERT INTO items (itemdate, itemtype, name, amount) VALUES(?,?,?,?)""", itemdate, itemtype, name, amount)
		
		return redirect(url_for("add"))


	else: 
	
		return render_template("add.html", title = title)
	cnxn.commit() 
	cnxn.close()
@app.route('/remove', methods=["GET", "POST"])
def remove():
	if request.method == "POST":
		#get info
		itemID = int(request.form.get("itemID"))
		
		cursor = cnxn.cursor()
		cursor.execute("""DELETE FROM items WHERE itemID =? """, itemID)
		return redirect(url_for("remove"))

	else: 
	
		return render_template("remove.html")
	cnxn.commit() 
	cnxn.close()


@app.route('/bar')
def bar():
	title = "Incomes and expenses by month"
	cursor = cnxn.cursor()
	sql = """SELECT * FROM [fin].[dbo].[items] ORDER BY  itemdate DESC"""
	df = pd.read_sql(sql, cnxn)
	df['itemdate'] = pd.to_datetime(df['itemdate'], errors='coerce')
	df = df.set_index(['itemdate'])
	df2= df.groupby([pd.TimeGrouper('M'), 'itemtype'])['amount'].sum()

	df3=df2.to_frame()
	typeis = type(df3)

	list_amount =df3['amount'].tolist()
	income_amount = []
	expense_amount = []
	for j in range(0, len(list_amount)):
		if j%2 == 0:
			expense_amount.append(list_amount[j])
		else:
			income_amount.append(list_amount[j])



	#print(df2.to_string())
	df4=df2.index.get_level_values('itemdate').to_series().apply(lambda x: dt.datetime.strftime(x, '%b %Y')).tolist()
	list_date=[]
	for i in range(0, len(df4)):
		if i%2 ==0:
			list_date.append(df4[i])

	trace1 = go.Bar(
    x=list_date,
    y=income_amount,
    name='Incomes',
    marker=dict(
        color='rgb(55, 83, 109)'
    )
	)
	trace2 = go.Bar(
	    x=list_date,
	    y=expense_amount,
	    name='Expenses',
	    marker=dict(
	        color='rgb(26, 118, 255)'
	    )
	)
	data = [trace1, trace2]
	layout = go.Layout(
	   
	    xaxis=dict(
	        tickfont=dict(
	            size=14,
	            color='rgb(107, 107, 107)'
	        )
	    ),
	    yaxis=dict(
	        title='USD',
	        titlefont=dict(
	            size=16,
	            color='rgb(107, 107, 107)'
	        ),
	        tickfont=dict(
	            size=14,
	            color='rgb(107, 107, 107)'
	        )
	    ),
	    legend=dict(
	        x=0,
	        y=1.0,
	        bgcolor='rgba(255, 255, 255, 0)',
	        bordercolor='rgba(255, 255, 255, 0)'
	    ),
	    barmode='group',
	    bargap=0.15,
	    bargroupgap=0.1
	)

	fig = go.Figure(data=data, layout=layout)

	barchart = plotly.offline.plot(fig, output_type="div", show_link=False, link_text=False)
	
	return render_template("bar.html", title = title, barchart = barchart)



if __name__=="__main__":
    app.run()
