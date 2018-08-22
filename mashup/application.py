import os
import re
from flask import Flask, jsonify, render_template, request

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")


@app.route("/articles")
def articles():
    """Look up articles for geo"""

    location = request.args.get("geo")
    if not location:
        raise RuntimeError("missing geo")

    result = lookup(location)
    if len(result) == 0:
        raise RuntimeError("the place is not in USA")
    # else:
        # new_result = []
        # for i in range(5):
            # new_result.append(result[i])

    return jsonify(result)


@app.route("/search")
def search():
    """Search for places that match query"""
    q = request.args.get("q")

    # https://www.sqlite.org/fts3.html
    # not so sure about the algorithm behind the scenes, however it seems to work well! Better than staff's solution since there
    # are a few that don't belong to the right search, such as q=101
    # virtual table
    result = db.execute("SELECT * FROM search WHERE search MATCH :q ORDER BY RANDOM() LIMIT 10", q=q)

    # return a json object
    return jsonify(result)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY country_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    return jsonify(rows)
