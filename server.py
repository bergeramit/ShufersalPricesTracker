
from flask import *
import pandas as pd
app = Flask(__name__)

@app.route("/tables")
def show_tables():
    data = pd.read_csv("C:\\Users\\berge\\OneDrive\\שולחן העבודה\\HST\\ShufersalPricesTracker\\price_track_2_11.csv")
    return render_template('view.html',tables=[prices.to_html(classes='prices')