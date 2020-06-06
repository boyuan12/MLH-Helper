from flask import Flask, redirect, request, render_template, jsonify, send_file, send_from_directory, jsonify
import requests
from datetime import date
import sqlite3

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
c = conn.cursor()

BASE_URL = "http://0.0.0.0:1234"

app = Flask(__name__)

SECRET_KEY="secretkey"

def calculateAge(birthDate):
    today = date.today()
    age = today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))

    return age

def randomdigit(digit=15):
    digits = ""
    import random
    import string
    for i in range(digit):
        digits += random.choice(string.digits)
    return digits

@app.route("/<string:d_id>")
def index(d_id):
    return redirect(f"https://my.mlh.io/oauth/authorize?client_id=a8639dbe3cdb080deec755f1d2f766df95f733824b8ca723f7af775137ca89d1&redirect_uri=http%3A%2F%2F0.0.0.0%3A1234%2Foauth%2Fauthorized%3Fdiscord_id%3D{d_id}&response_type=token")

@app.route("/oauth/authorized")
def authorized():
    if not request.args.get("access_token"):
        return render_template("authorized.html")
    user = requests.get("https://my.mlh.io/api/v2/user.json?access_token=" + request.args.get("access_token")).json()

    if user["status"] != "OK":
        return "There's a problem with Oauth your MLH account, please ask admin for help or try again later"

    exist = c.execute("SELECT * FROM users WHERE user_id=:u_id", {"u_id": int(user["data"]["id"])}).fetchall()

    if len(exist) != 0:
        return redirect(f"/hackathon?user_id={exist[0][0]}")

    dob = user["data"]["date_of_birth"].split("-")
    age = calculateAge(date(int(dob[0]), int(dob[1]), int(dob[2])))
    c.execute("INSERT INTO users (user_id, first_name, last_name, phone, email, age, student, discord_id, gender, school) VALUES (:u_id, :f_name, :l_name, :phone, :email, :age, :student, :d_id, :gender, :school)", {"u_id": user["data"]["id"], "f_name": user["data"]["first_name"], "l_name": user["data"]["last_name"], "phone": user["data"]["phone_number"], "email": user["data"]["email"], "age": age, "student": user["data"]["level_of_study"], "d_id": request.args.get("d_id"), "gender": user["data"]["gender"], "school": user["data"]["school"]["name"]})
    conn.commit()
    return redirect(f'/information?user_id={user["data"]["id"]}')

@app.route("/information", methods=["GET", "POST"])
def information():
    if request.method == "POST":
        print(request.form.get("region"))
        c.execute("UPDATE users SET region=:region, street_address=:sa, city=:city, zip=:zip, country=:country WHERE user_id=:u_id", {"region": request.form.get("region"), "sa": request.form.get("sa"), "city": request.form.get("city"), "zip": request.form.get("zip"), "country": request.form.get("country"), "u_id": request.args.get("user_id")})
        conn.commit()
        return redirect(f"/hackathon?user_id={request.args.get('user_id')}")
    else:
        return render_template("information.html")

@app.route("/hackathon", methods=["GET", "POST"])
def hackathon():
    if request.method == "POST":
        exist = c.execute("SELECT * FROM hackathons WHERE user_id=:u_id AND hackathon=:h", {"u_id": request.args.get("user_id"), "h": request.form.get("hackathon")}).fetchall()

        if len(exist) != 0:
            return "you already registered"
        c.execute("INSERT INTO hackathons (user_id, hackathon) VALUES (:u_id, :h)", {"u_id": request.args.get("user_id"), "h": request.form.get("hackathon")})
        conn.commit()
        return "you are done! send a message to the bot and verify!"

    else:
        events = c.execute("SELECT * FROM hackathons WHERE user_id=:u_id", {"u_id": request.args.get("user_id")}).fetchall()
        hackathon = requests.get("https://mlh-events.now.sh/na-2020").json()
        hackathons = []


        from datetime import datetime

        for i in hackathon:
            hacka = datetime.strptime(i["endDate"], "%Y-%m-%d") # "%d/%m/%Y"
            present = datetime.now()
            if hacka.date() > present.date():
                hackathons.append(i["name"])
            else:
                break
        return render_template("hackathon.html", events=events, hackathon=hackathons)

@app.route("/api/generate/<string:hack>/<string:secret_key>")
def generate(hack, secret_key):
    d = {} # {"user_id": {"user_id": }}
    if secret_key != SECRET_KEY:
        return "403"
    hacks = c.execute("SELECT user_id FROM hackathons").fetchall()
    for i in hacks:
        user = c.execute("SELECT * FROM users WHERE user_id=:id", {"id": i[0]}).fetchall()[0]
        d[str(user[0])] = {"user_id": user[0], "region": user[1], "first_name": user[2], "last_name": user[3], "phone": user[4], "email": user[5], "age": user[6], "student": user[7], "street_address": user[8], "city": user[9], "zip": user[10], "country": user[11], "discord_id": user[12], "gender": user[13], "school": user[14]}
    import csv
    digit = randomdigit()
    with open(f'static/{digit}.csv', mode='w') as csv_file:
        fieldnames = ['user_id', 'region', 'first_name', "last_name", "phone", "email", "age", "student", "street_address", "city", "zip", "country", "discord_id", "gender", "school"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for i in d:
            writer.writerow(d[i])

        return jsonify(url=f"{BASE_URL}/static/{digit}.csv")


@app.route("/api/current_hack/<string:d_id>")
def current_hack_api(d_id):
    user = c.execute("SELECT user_id FROM users WHERE discord_id=:d_id", {"d_id": d_id}).fetchall()
    if len(user) == 0:
        return jsonify(resp="You didn't register an account, please go register first! Remember to type tag the bot and type checkin to get your link to sign up!")
    user_id = user[0][0]
    hack = c.execute("SELECT * FROM hackathons WHERE user_id=:u_id", {"u_id": user_id}).fetchall()
    if len(hack) == 0:
        return jsonify(resp="You didn't checkin to a hackathon, please go checkin first! Remember to type tag the bot and type checkin to get your link to checkin!")
    hacks = requests.get("https://mlh-events.now.sh/na-2020").json()
    for i in hacks:
        if i["name"] == hack[0][1]:
            return jsonify(resp=f"Welcome to {i['name']}! The location is at {i['location']} (Due to COVID Pandemic, it's the timeframe). {i['name']} starts at {i['startDate']}, ends at {i['endDate']}. Be sure to checkin on their website also! Located at {i['url']}. Enjoy!\n{i['imageUrl']}", hack=i["name"])


if __name__ == "__main__":
    app.run("0.0.0.0", 1234, True)