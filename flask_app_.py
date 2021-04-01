##CS205 Final Project 
##Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

##Beginning of the flask app for the interface of the project

from flask import Flask, render_template, request

app = Flask(__name__)

username = ""


@app.route("/")
def home():
    return render_template("main_page.html", u_name = username)


@app.route("/about")
def about():
    return render_template("about_us.html")


@app.route("/sign_in", methods=['POST'])
def sign_in():
    global username
    valid_user = None
    username = request.form['username']
    #here, we query the database for the username
    #if the username is found, we load the users data in to a class to then display
        #return render_template(the "successful sign in" page)
    #else, we tell the user we could not find their username

    #just for now, I'll make this if/else clause
    #If username is valid, go to next page
    if username == "user1":
        return render_template("successful_sign_in.html", u_name=username, valid_user=valid_user)
    #if username is not valid, stay on login in page and show the user their username
    #is not valid
    else:
        valid_user = False
        return render_template("main_page.html", u_name=username, valid_user=valid_user)

@app.route("/selection", methods=['POST'])
def decision():
    choice = request.form['selection']
    if choice == "display":
        #display the users cards
        return render_template("display_cards.html")
    elif choice == "buy":
        #allow the user to look at more cards to buy
         return render_template("buy_cards.html")
    else:
        #display the trading interface
         return render_template("trade_cards.html")


if __name__ == "__main__":
    app.run()
