from flask import Flask, render_template, request, redirect, url_for
from utils.fetch_weather_data import get_weather
from pymongo import MongoClient
from datetime import datetime
from utils.convert import convert
from apscheduler.schedulers.background import BackgroundScheduler

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io

from bson import ObjectId


app = Flask(__name__)
app.debug = True

client = MongoClient("mongodb://localhost:27017")
db = client['tenerife']
weather_collection = db['weather'] 
tasks_collection= db['tasks']

print(weather_collection)



def save_to_monogdb(x):
     
     current_weather = {
        "area":x['name'],
        "temp": convert(x['main']['temp']),
        "temp_min":convert(x['main']['temp_min']),
        "temp_max":convert(x['main']['temp_max']),
        "pressure":x['main']['pressure'],
        "humidity":x['main']['humidity'],
        "timestramp":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "desc":f"{x['weather'][0]['main']},{x['weather'][0]['description']}"        
        }
     

     weather_collection.insert_one(current_weather)

def job():
    data = get_weather() # dane pogodowe
    if(data):
        save_to_monogdb(data)
        print("Dostarczono nowe dane")
    else:
        print("NIe udało się pobrać danych")
    

scheduler = BackgroundScheduler()
scheduler.add_job(job, 'interval', minutes=15)
scheduler.start()



@app.route("/")
def homepage():
    latest_data = weather_collection.find().sort([('_id',-1)]).limit(30)

    return render_template("index.html", weather_documents=list(latest_data))


@app.route('/chart')
def generate_chart():
    chart_data = weather_collection.find({}, {'_id':0, 'temp':1, 'timestramp':1}).sort([('_id',-1)]).limit(5)
    data = list(chart_data)
    
    timestamps =[datetime.strptime(entry['timestramp'], "%Y-%m-%d %H:%M:%S").day for entry in data]
    temperatures = [entry["temp"] for entry in data]
    fig = Figure()
    axis = fig.add_subplot(1,1,1)
    axis.plot(timestamps, temperatures)
    axis.set_xlabel("Time")
    axis.set_ylabel("Temperature")
    axis.set_title("Tenerife weather")
    axis.set_xticks(timestamps)

    canvas = FigureCanvasAgg(fig)
    png = io.BytesIO()
    canvas.print_png(png)


    return png.getvalue(), 200, {"Content-Type":"image/png"}





@app.route('/add-task', methods=["POST"])
def add_task():
   
    title = request.form.get("title")
    desc = request.form.get("desc")
    category = request.form.get("category")
    urgency = request.form.get("urgency")

    new_task = {
        "title":title,
        "desc":desc,
        "category":category,
        "urgency":urgency
    }

    try:
         tasks_collection.insert_one(new_task)
    
    except Exception as e:
        return "Błąd" + str(e)


    return redirect(url_for("tasks")) # przekierowanie na inną stronę



@app.route("/delete-task/<id>", methods=["POST"])
def delete_task(id):

    try:
        tasks_collection.delete_one({"_id":ObjectId(id)})
    except Exception as e:
        return "Błąd" + str(e)
    
    return redirect(url_for("tasks"))




@app.route("/tasks")
def tasks():
    
    tasks = list(tasks_collection.find())

    return render_template("tasks.html", tasks=tasks)









