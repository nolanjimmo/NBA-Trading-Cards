# CS205 Final Project
# Charles Morgan, Nolan Jimmo, Dean Stuart, George Fafard

# Beginning of the flask app for the interface of the project
from datetime import datetime

from flask import flash, render_template, request, redirect, url_for
from flask_login import current_user, login_user, login_required, logout_user

from app import app
from app import login_db as db, login_helper as dc
from app.query_engine import QueryEngine, User, NoOutputError

current_user: User


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        QueryEngine.update_user_last_seen(current_user)


@app.route("/", methods=['GET', 'POST'])
@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    user_cards = QueryEngine.get_user_cards(current_user.unique_id)
    num_user_cards = len(user_cards)
    user_trades = QueryEngine.get_user_trades(current_user.unique_id)
    return render_template('dashboard.html', title="Dashboard", user_cards=user_cards, num_user_cards=num_user_cards,
                           user_trades=user_trades)


@app.route("/add_cards", methods=['GET', 'POST'])
@login_required
def add_cards():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        success: bool = QueryEngine.add_card_to_user(current_user.unique_id, card_id)
        if not success:
            flash("You need to remove a card from your deck before adding a new one!")
            return redirect(url_for('dashboard'))
        return redirect(url_for('dashboard'))
    available_cards = QueryEngine.get_available_cards()
    return render_template("add_cards.html", title="Add Cards", available_cards=available_cards)


@app.route("/remove_card", methods=['GET', 'POST'])
@login_required
def remove_card():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        if card_id in current_user.cards:
            QueryEngine.remove_card_from_user(current_user.unique_id, card_id)
        return redirect(url_for('dashboard'))


@app.route("/view_card", methods=['GET', 'POST'])
@login_required
def view_card():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        card = QueryEngine.get_card_from_id(card_id)
        return render_template("view_card.html", title="View Card", card=card)


@app.route("/create_trade", methods=['GET', 'POST'])
@login_required
def create_trade():
    if request.method == 'POST':
        own_card_ids = request.form.getlist('own_cards')
        other_card_ids = request.form.getlist('other_cards')
        other_user_id = request.form.get('other_user_id')
        if QueryEngine.create_trade(current_user.unique_id, own_card_ids, other_user_id, other_card_ids):
            return redirect(url_for('dashboard'))
        else:
            flash("Failed to create trade")
            return redirect(url_for('create_trade'))
    users = QueryEngine.get_all_users()
    return render_template("create_trade.html", title="Create Trade", users=users)


@app.route("/choose_user", methods=['GET', 'POST'])
@login_required
def choose_user():
    if request.method == 'POST':
        users = QueryEngine.get_all_users()
        username = request.form.get('users')
        own_cards = QueryEngine.get_user_cards(current_user.unique_id)
        other_user = QueryEngine.get_user_from_username(username)
        other_cards = QueryEngine.get_user_cards(other_user.unique_id)
        return render_template("create_trade.html", title="Create Trade", users=users, own_cards=own_cards,
                               other_user=other_user, other_cards=other_cards)


@app.route("/view_trade", methods=['GET', 'POST'])
@login_required
def view_trade():
    if request.method == 'POST':
        trade_id = request.form.get('trade_id')
        trade = QueryEngine.get_trade_from_id(trade_id)
        user1 = QueryEngine.get_user_from_id(trade.user1_id)
        user1_cards = []
        for card_id in trade.user1_cards:
            user1_cards.append(QueryEngine.get_card_from_id(card_id))
        user2 = QueryEngine.get_user_from_id(trade.user2_id)
        user2_cards = []
        for card_id in trade.user2_cards:
            user2_cards.append(QueryEngine.get_card_from_id(card_id))
        return render_template("view_trade.html", title="View Trade", trade=trade, user1=user1, user1_cards=user1_cards,
                               user2=user2, user2_cards=user2_cards)


@app.route("/confirm_trade", methods=['GET', 'POST'])
@login_required
def confirm_trade():
    if request.method == 'POST':
        trade_id = request.form.get('trade_id')
        trade = QueryEngine.get_trade_from_id(trade_id)
        if QueryEngine.user_confirm_trade(current_user, trade):
            return redirect(url_for('dashboard'))
        else:
            flash("You must drop enough players before you are able to confirm this trade")
            return redirect(url_for('dashboard'))


@app.route("/view_users", methods=['GET', 'POST'])
@login_required
def view_users():
    users = QueryEngine.get_all_users()
    return render_template("view_users.html", title="View Users", users=users)


@app.route("/view_user", methods=['GET', 'POST'])
@login_required
def view_user():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = QueryEngine.get_user_from_id(user_id)
        user_cards = QueryEngine.get_user_cards(user_id)
        user_trades = QueryEngine.get_user_trades(user_id)
        return render_template("view_user.html", title="View User", user=user, user_cards=user_cards,
                               user_trades=user_trades)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me')

        search_results = db.search_pass(username)
        if search_results == -1:
            flash("Incorrect username or password")
            return redirect(url_for('login'))
        elif dc.authenticate(search_results, password):
            try:
                user = QueryEngine.get_user_from_username(username)
            except NoOutputError:
                flash("Incorrect username or password")
                return redirect(url_for('login'))
            else:
                login_user(user, remember=remember_me)
                next_page = request.args.get('next_page')
                if not next_page:
                    next_page = url_for('dashboard')
                return redirect(next_page)
        else:
            flash("Incorrect username or password")
            return redirect(url_for('login'))
    return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('dashboard'))


@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if dc.is_good_user(username) and dc.is_good_pass(password):
            if not QueryEngine.check_user_exists(username):
                if db.register_user(username, password, 1) != -1:
                    flash("Successfully create user", "alert-success")
                    return redirect(url_for('login'))
                else:
                    flash("Unable to create new user", "alert-danger")
                    return redirect(url_for('sign_up'))
            else:
                flash("User already exists with that Username", "alert-danger")
                return redirect(url_for('sign_up'))
        else:
            flash("Username or Password not valid", "alert-danger")
            return redirect(url_for('sign_up'))
    return render_template("sign_up.html", title="Sign Up")
