##CS205 Final Project 
##Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

##Beginning of the flask app for the interface of the project

import traceback

from flask import Flask, flash, render_template, request, redirect, url_for
from query_engine import *

db_filename = "trading_card_data.db"
schema_filename = "trading_card_schema.sql"

if os.path.exists(db_filename):
    os.remove(db_filename)
load_database(db_filename, schema_filename)
###Test data for the database
qe = QueryEngine(db_filename)
load_test_data(qe)

app = Flask(__name__)
app.secret_key = "final_project"

username = ""
curr_user = None


@app.route("/")
def home():
    return render_template("main_page.html", u_name=username)


@app.route("/about")
def about():
    return render_template("about_us.html")


@app.route("/sign_in", methods=['POST','GET'])
def sign_in():
    qe = QueryEngine(db_filename)
    global username
    global curr_user
    valid_user = None
    try:
        username = request.form['username']
    except:
        return render_template("main_page.html", u_name=None)
    #here, we query the database for the username
    try:
        curr_user = qe.get_user_from_username(username)
        return render_template("successful_sign_in.html", u_name=username, valid_user=valid_user)
    except:
        valid_user = False
        return render_template("main_page.html", u_name=username, valid_user=valid_user)


@app.route("/sign_up", methods=['POST'])
def sign_up():
    qe = QueryEngine(db_filename)
    global username
    global curr_user
    valid_user = None
    user_exists = False
    username = request.form['username']

    if not qe.does_user_exist(username):
        qe.add_user(username, [], [])
    else:
        user_exists = True

    if not user_exists:
        curr_user = qe.get_user_from_username(username)
        return render_template("successful_sign_in.html", u_name=username, valid_user=valid_user)
    else:
        return render_template("main_page.html", u_name=username, valid_user=valid_user, user_exists=user_exists)


@app.route("/successful_sign_in", methods=['POST','GET'])
def successful_sign_in():
    global username
    return render_template("successful_sign_in.html", u_name=username, valid_user=True)

@app.route("/selection", methods=['POST'])
def decision():
    qe = QueryEngine(db_filename)
    choice = request.form['selection']
    if choice == "display":
        card_list = []
        # Create player classes for each of the player cards that the user has
        # Store them in a list, then pass that list to the render_template()
        card_list = qe.get_user_cards(curr_user.id)
        # display the users cards by passing list to display_cards.html
        return render_template("display_cards.html", c_list=card_list, length=len(card_list))

    elif choice == "buy":
        #all_cards = qe.get_all_cards()
        # allow the user to look at all cards available
        #return render_template("buy_cards.html", all_cards=all_cards, qe=qe)
        return redirect(url_for("buying_cards"))
    else:
        #trade_list=[]
        #Here, we are going to display the list of trades the user is currently involved in
        #for trade in curr_user.trades:
            #trade_list.append(qe.get_trade_from_id(trade))
        #display the trading interface
        #return render_template("trade_cards.html", t_list=trade_list, qe=qe, c_user=curr_user)
        return redirect(url_for("trade_interface"))

@app.route("/buying_cards", methods=['POST','GET'])
def buying_cards():
    global curr_user
    qe = QueryEngine(db_filename)
    curr_user = qe.get_user_from_username(username)
    user_cards = qe.get_user_cards(curr_user.id)
    all_cards = qe.get_all_cards()
    rm_success = None

    try:
        add_player = request.form['add']
        if len(curr_user.cards) >= 5:
            try:
                drop_player = request.form['drop']
                rm_success = remove_card(drop_player)
            except:
                print("input was bad")
                #print(traceback.print_exc())
                return render_template("buy_cards.html", all_cards=all_cards, u_cards=user_cards, qe=qe)
        if rm_success != False:
            add_new_card(add_player)
        else:
            print("here")
            flash("You can't add a player without dropping one")
            return render_template("buy_cards.html", all_cards=all_cards, u_cards=user_cards, qe=qe)
        user_cards = qe.get_user_cards(curr_user.id)
        all_cards = qe.get_all_cards()
        return render_template("successful_sign_in.html", u_name = username, valid_user = True)
        #return render_template("buy_cards.html", all_cards=all_cards, u_cards=user_cards, qe=qe)
    except:
        #print(traceback.print_exc())
        return render_template("buy_cards.html", all_cards=all_cards, u_cards=user_cards, qe=qe)

def add_new_card(card_name):
    qe = QueryEngine(db_filename)
    new_card = qe.get_card_from_name(card_name)
    qe.add_card_to_user(curr_user.id, new_card.id)

def remove_card(card_name) -> bool:
    qe = QueryEngine(db_filename)
    try:
        temp_card = qe.get_card_from_name(card_name)
    except:
        return False
    for card in curr_user.cards:
        if card == temp_card.id:
            qe.remove_card_from_user(curr_user.id, card)
            return True
    return False

@app.route("/trade_cards", methods=['POST','GET'])
def trade_interface():
    global curr_user

    qe = QueryEngine(db_filename)
    curr_user = qe.get_user_from_username(username)
    trade_list = get_trade_list()
    trade_success = False

    try: 
        trade_id = int(request.form['trade_id'])
        if trade_id in curr_user.trades:
            trade_success = qe.do_trade(trade_id)
        #print(trade_success)
        if trade_success == True:
            return render_template("successful_sign_in.html", u_name = username, valid_user = True)
        else:
            return render_template("trade_cards.html", t_list=trade_list, qe=qe, c_user=curr_user, rft=True, ts=False)
    except:
        #print(traceback.print_exc())
        try:
            #here, we see if there is any input in the propose trade area
            other_user = request.form['other_user']
            u1_player = request.form['u1_player']
            u2_player = request.form['u2_player']
            qe.create_trade(curr_user.id, [qe.get_card_from_name(u1_player).id], 
                    qe.get_user_from_username(other_user).id,[qe.get_card_from_name(u2_player).id])
            return render_template("successful_sign_in.html", u_name = username, valid_user = True)
        except:
            #if there is nothing in either input sections, we just display the page again
            print(traceback.print_exc())
            return render_template("trade_cards.html", t_list=trade_list, qe=qe, c_user=curr_user, rft=False, ts=False)

def get_trade_list():
    qe = QueryEngine(db_filename)
    trade_list=[]
        #Build the list of trades the user is involved in
    for trade in curr_user.trades:
        trade_list.append(qe.get_trade_from_id(trade))
    return trade_list
            


if __name__ == "__main__":
    app.run()
