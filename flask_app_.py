##CS205 Final Project 
##Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

##Beginning of the flask app for the interface of the project

from flask import Flask, render_template, request
from query_engine import *

db_filename = "trading_card_data.db"
schema_filename = "trading_card_schema.sql"

if os.path.exists(db_filename):
        os.remove(db_filename)
load_database(db_filename, schema_filename)
###Test data for the database
load_test_data(db_filename)

app = Flask(__name__)

username = ""
curr_user = None


@app.route("/")
def home():
    return render_template("main_page.html", u_name = username)


@app.route("/about")
def about():
    return render_template("about_us.html")


@app.route("/sign_in", methods=['POST'])
def sign_in():
    qe = QueryEngine(db_filename)
    global username
    global curr_user
    valid_user = None
    username = request.form['username']
    #here, we query the database for the username
    try:
        curr_user = qe.get_user_from_username(username)
        return render_template("successful_sign_in.html", u_name=username, valid_user=valid_user)
    except:
        valid_user = False
        return render_template("main_page.html", u_name=username, valid_user=valid_user)

@app.route("/selection", methods=['POST'])
def decision():
    qe = QueryEngine(db_filename)
    choice = request.form['selection']
    if choice == "display":
        card_list = qe.get_user_cards(curr_user.id)
        #display the users cards by passing list to display_cards.html
        return render_template("display_cards.html", c_list=card_list)
    elif choice == "buy":
        #allow the user to look at more cards to buy
         return render_template("buy_cards.html")
    else:
        #display the trading interface
         return render_template("trade_cards.html")


if __name__ == "__main__":
    app.run()
