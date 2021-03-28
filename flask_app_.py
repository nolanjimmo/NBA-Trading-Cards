##CS205 Final Project 
##Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

##Beginning of the flask app for the interface of the project

from flask import Flask, render_template

app = Flask(__name__)

button_state = False


@app.route("/")
def home():
    return render_template("main_page.html", b_state=button_state)


@app.route("/about")
def about():
    return render_template("about_us.html")


@app.route("/switch_state/", methods=['POST'])
def flip_button_state():
    global button_state
    if button_state:
        button_state = False
    else:
        button_state = True
    return render_template("main_page.html", b_state=button_state)


if __name__ == "__main__":
    app.run()
