from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Restaurant Reservation Website"

app.run()