from flask import Flask, request, redirect, render_template
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import random
import string
import datetime

load_dotenv()
mongoconnect = os.getenv('MONGO_URL')
client = MongoClient(mongoconnect)
db = client['short_url']
collection = db['urls']
collection.create_index("expiry", expireAfterSeconds=0)

app = Flask(__name__)


def exixting_url(url):
    now = datetime.datetime.utcnow()
    entry = collection.find_one({
        'url': url,
        'expiry': {"$gt": now}
    })
    return entry['short_code'] if entry else None


def genrate_unique_code(length=7):
    while True:
        code = "".join(random.choices(string.ascii_letters + string.digits, k=length))
        if not collection.find_one({"short_code": code}):
            return code


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        expiry_time = int(request.form['expiryurl'])
        short_code = exixting_url(url)
        if not short_code:
            short_code = genrate_unique_code()
            expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry_time)
            collection.insert_one({
                'short_code': short_code,
                'url': url,
                'expiry': expiry
            })
        short_url = request.host_url + short_code
        return render_template('result.html', shorturl=short_url, expiry=expiry_time)
    return render_template('index.html')


@app.route('/<short_code>')
def redirect_to_url(short_code):  
    entry = collection.find_one({"short_code": short_code})
    if entry:
        if entry["expiry"] > datetime.datetime.utcnow():
            return redirect(entry["url"])
        else:
            collection.delete_one({"short_code": short_code})
            return "This link is expired", 410
    return "Short code not found", 404


if __name__ == "__main__":
    app.run(debug=True)
