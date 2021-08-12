
from flask import *
from authenticator import Authenticator
from mongodriver import MongoDriver
from matcher import Matcher
from flask_cors import CORS, cross_origin

from pymongo.mongo_client import MongoClient
#from communication_handler import *
from flask_socketio import *
import sys
import json


# App Initialization
app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = "8259652858"
socketio.init_app(app, cors_allowed_origins="*")

# Object Initialization
driver = MongoDriver()
authenticator = Authenticator(driver)
matcher = Matcher(driver)
driver.watched_by(matcher)


# Load questionarie questions from json file
with open("./static/questions.json") as qs:
    questions = json.load(qs)

def user_sanity_check():
    """
    Check the browser cookie and the login status of the user with the given email 
    Whitelist users with a cookie and login status set to true
    Returns False if the user does not have a cookie, or has login status as false
    """
    user_email = driver.get_email_with_cookie(request.cookies.get('session_id'))
    
    if not user_email:
        return False
    return authenticator.get_user_login_status(user_email)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Landing page
    # Check if they have a cookie
    email = driver.get_email_with_cookie(request.cookies.get('session_id'))
    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    if email is not None and driver.is_user_verified(email):

        if driver.is_user_finished_survey(user_id):
            # Redirect them to the rest of the app
            return redirect("/home")
        else:
            # Redirect them to the questionair page
            return redirect("/questionnaire")

    # Else, redirect them to the login page
    return redirect("/login")

@app.route('/login', methods=['GET', 'POST'])
def sign_in():

    if user_sanity_check():
        # User is already logged in
        return redirect("/home")

    if request.method == "POST":

        # Extract information from the sign-in form
        form = request.form
        email_id = form["email"]
        password = form["password"]

        if form["submit"] == 'Register Now!':
            # User clicked on the register button, redirect them to that page
            return redirect("/register")

        if email_id != "" and password != "":
            
            response_code = authenticator.authenticate(email_id, password)
            if response_code == 0:
                # Credentials are good, redirect them to the rest of the app
                # Set this user as logged in
                authenticator.set_user_login_status(email_id, True)
                # Redirect them to the rest of the app page
                redirect_response = make_response(redirect("/home"))
                # Set the user's browser cookie to the unique cookie id
                redirect_response.set_cookie('session_id', driver.get_cookie_with_email(email_id))
                return redirect_response
            elif response_code == 1:
                # User did not verify their email
                authenticator.resend_verification_code(email_id)
                # Redirect them to the verification page
                redirect_response = make_response(redirect("/verify"))
                # Set the user's browser cookie to the unique cookie id
                redirect_response.set_cookie('session_id', driver.get_cookie_with_email(email_id))
                return redirect_response
            else:
                # Login credentials are invalid
                return render_template("login.html", status="Invalid login.")
        else:
            # User left one of the fields empty
            return render_template("login.html", status="Email or password field is empty.")

    if "pchange" in request.args:
        # Render the login page with password change message
        return render_template("login.html", pchange=request.args["pchange"])
    else:
        # Render the login page
        return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():

    if user_sanity_check():
        # User is already logged in
        return redirect("/home")

    if request.method == "POST":

        # Extract information from the sign-in form
        form = request.form
        email_id = form["email"]
        username = form["username"]
        password = form["password"]
        password2 = form["password2"]

        if email_id != "" and password != "":
            
            if password != password2:
                # Passwords do not match
                return render_template("register.html", status="Passwords do not match.")

            # Register the user and add them to the database
            response = authenticator.register(email_id, username, password)

            # Refer to authenticator's register function for meaning of code
            if response == 1:
                # Email is already in use
                return render_template("register.html", status="Email ID is already in use.")
            elif response == 2:
                # Email is not UofT email
                return render_template("register.html", status="Email ID is not an UofT email.")
            elif response == 3:
                # Password too short
                return render_template("register.html", status="Password needs to be at least 8 characters long.")
            elif response == 4:
                # Username in use
                return render_template("register.html", status="Username is already in use.")
            else:
                # The response returned by the authenticator is a unique cookie id for the user
                redirect_response = make_response(redirect("/verify"))
                # Set the user's browser cookie to the unique cookie id
                redirect_response.set_cookie('session_id', response)
                return redirect_response

        else:
            # User left one of the fields empty            
            return render_template("register.html", status="Email or password field is empty.")

    # Render the register page
    return render_template("register.html")

@app.route('/verify', methods=['GET', 'POST'])
def verify():

    if user_sanity_check():
        # User is already logged in
        return redirect("/home")

    if request.method == "POST":

        # Extract information from the sign-in form
        form = request.form
        code = form["code"]
        email = driver.get_email_with_cookie(request.cookies.get('session_id'))

        if form["submit"] == "Resend Code":
            # User clicked on the resend code button
            authenticator.resend_verification_code(email)
            # Notify the user that the code has been resent
            return render_template("verify.html", resend_status="Resent a new verification code")

        if code != "":

            if form["submit"] == "Submit":
                if authenticator.check_verification_code(email, code):
                    # Set this user as logged in
                    authenticator.set_user_login_status(email, True)
                    # Redirect to rest of the app
                    return redirect("/home")
                else:
                    # The code was not correct, resend a new code to them
                    authenticator.resend_verification_code(email)
                    return render_template("verify.html", code_status="Incorrect code. Resending new code.")
        else:
            # User left the code text box blank
            return render_template("verify.html", code_status="Please enter the verification code.")

    # Render the verify page
    return render_template("verify.html")

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == "POST":

        # Extract information from the sign-in form
        form = request.form
        email = form["email"]
        code = form["code"]

        if email == "":
            # Email is empty
            return render_template("forgot-password.html", status="Please enter your email.")

        if driver.find_one("auth", {"email_id": email}) is None:
            # Email does not exist
            return render_template("forgot-password.html", status="Email does not exist.")

        if form["submit"] == "Send Code":
            # User clicked on the resend code button
            authenticator.resend_verification_code(email)
            # Notify the user that the code has been resent
            return render_template("forgot-password.html", resend_status="Sent a new verification code", email_id=email)
        
        if form["submit"] == "Submit":
            if code == "":
                # User did not enter code
                return render_template("forgot-password.html", status="Please enter the code.", email_id=email)
            
            if authenticator.check_verification_code(email, code):
                cookie = driver.get_cookie_with_email(email)
                # The response returned by the authenticator is a unique cookie id for the user
                redirect_response = make_response(redirect("/change_password"))
                # Set the user's browser cookie to the unique cookie id
                redirect_response.set_cookie('session_id', cookie)
                return redirect_response
            else:
                # The code was not correct, resend a new code to them
                authenticator.resend_verification_code(email)
                return render_template("forgot-password.html", email_id=email, status="Incorrect code. Resending new code.")

        return redirect("/change_password")

    # Render the page
    return render_template("forgot-password.html")

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():

    if request.method == "POST":
        form = request.form
        password = form["password"]
        password2 = form["password2"]
        email = driver.get_email_with_cookie(request.cookies.get('session_id'))

        if password == "":
            # Password is empty
            return render_template("change-password.html", status="Please enter your new password.")

        if password != password2:
            # Password does not match
            return render_template("change-password.html", status="Password does not match.")

        # Update the database
        if authenticator.update_password(email, password):
            # Password has been updated
            authenticator.send_password_update_email(email)
            return redirect("/login")
        else:
            # Password is too short
            return render_template("change-password.html", status="Password needs to be atleast 8 characters.")

    # Render the page
    return render_template("change-password.html")


@app.route('/logout')
def logout():
    # Set this user as logged out
    authenticator.set_user_login_status(driver.get_email_with_cookie(request.cookies.get('session_id')), False)
    # Redirect the user to the logged out page
    logout_response = make_response(render_template("logout.html"))
    # Delete the user's cookie
    logout_response.delete_cookie('session_id')
    return logout_response

@app.route('/home')
def home():
    """
    This page must first check if user has finished the survey

    IF NO: MAKE THEM FINISH THE SURVEY!!

    IF YES: THEY GET A NAV BAR TO:
        MATCHES
        BIO
        LOG OUT
        ETC ...
    """

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    if driver.is_user_finished_survey(user_id):
        return redirect("/matches")
    else:
        return redirect("/questionnaire")

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    if request.method == "POST":
        # they have finished the survey
        results = []
        for key in request.form:
            results.append(int(request.form[key]))
        # print(driver.get_email_with_cookie(request.cookies.get('session_id')))
        user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
        for index, category in enumerate(["music", "movie", "game"]):
            driver.update_preferences(user_id, category, results[4 * index: 4 * index + 4])

        driver.set_user_finished_survey(user_id, 'quest')

        if driver.is_user_finished_survey(user_id):
            return redirect('/profile') # Change to profle link
        else:
            # User has not completed both surveys yet, redirect them to meme survey
            return redirect("/survey")
    else:
        # send them the questions
        return render_template("quest.html", question_list=questions)

@app.route('/survey', methods=['GET', 'POST'])
def memesurvey():

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    if request.method == "POST":
        # they have finished the survey
        results = []
        for key in request.form:
            results.append(int(request.form[key]))

        user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
        driver.update_preferences(user_id, "humor", results)
        
        driver.set_user_finished_survey(user_id, 'meme')

        return redirect('/profile') # Change to profle link

    return render_template("meme.html")

@app.route('/chatroom', methods=['GET', 'POST'])
def chat_room():
    # sanity check
    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")       
        
    # extract username
    userid = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    my_username = driver.get_username_from_userid(userid)

    roomid = None
    # matches page, private "Say Hi" button
    if 'sayhi' in request.form:
        other_user = request.form['sayhi']
        users = [my_username, other_user]

        # check if this room already exists
        if not driver.get_roomid_from_users("private", users):
            roomid = driver.create_new_private_room(users)

    # matches page, group "Join Group" button
    elif 'join-group' in request.form:
        roomid = request.form['join-group']

        # check if roomid exists
        if driver.find_one("rooms", {"roomid": roomid, "type": "group"}):
            driver.add_user_to_room(roomid, my_username)

    # create group request
    elif 'create-group' in request.form:
        groupname = request.form['group-name']
        other_user = request.form['create-group']
        users = [my_username, other_user]
        roomid = driver.create_new_group_room(groupname, users)

    # chatroom private "Talk" button
    elif 'open-chat' in request.form:
        roomid = request.form['open-chat']
    # chatroom group "Talk" button
    elif 'open-group' in request.form:
        roomid = request.form['open-group']
    elif 'match-open-chat' in request.form:
        other_user = request.form['match-open-chat']
        roomid = driver.get_roomid_from_users("private", [my_username, other_user])

    active_chats = driver.get_active_private_rooms(userid)
    active_groups = driver.get_active_group_rooms(userid)
    
    # default
    if roomid is None:
        if len(active_chats) == 0 and len(active_groups) == 0:
            return render_template('empty-chatroom.html')
        elif len(active_chats):
            roomid = next(iter(active_chats.keys()))
        elif len(active_groups):
            roomid = next(iter(active_groups.keys()))
            chatname = driver.get_group_name_from_roomid(roomid)
            
    
    type = driver.get_room_type(roomid)
    messages = driver.get_messages(roomid)
    blocklist = driver.get_blocklist(my_username)

    if 'status' in request.form:
        group_status = request.form['status']
        group_roomid = request.form['group-roomid']
        driver.update_group_privacy(group_roomid, group_status)
    
    if type == 'private':
        users = driver.find_one('rooms', {'roomid': roomid})['users']
        users.remove(my_username)
        chatname = users[0]
        return render_template('chatroom.html', username=my_username, room=roomid,  messages = messages, m = len(messages), active_chats = active_chats, active_groups=active_groups, curr_type = type, chatname=chatname, blocklist = blocklist)
    elif type == 'group':
       
        groupname = driver.get_group_name_from_roomid(roomid)
        
        return render_template('chatroom.html', username=my_username, room=roomid,  messages = messages, m = len(messages), active_chats = active_chats, active_groups=active_groups, curr_type = type, chatname=groupname, blocklist = blocklist)

@app.route('/matches', methods=['GET', 'POST'])
def matches():
    
    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    match_category = 'overall'  # by default match over all categories
    if request.method == 'POST' and 'match_category' in request.form:
        match_category = request.form['match_category']

    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    username = driver.get_username_from_userid(user_id)
    matches = matcher.get_matches(user_id, match_category)
    blocklist = driver.get_blocklist(username)

    # add bool to matches if they have a chat with this user
    active_chats = driver.get_active_private_rooms(user_id)
    
    # set of all the people we have chats with
    read = set(active_chats.values())
    # this is the set of all the names of our matches
    names_list = [m['username'] for m in matches]
    names = set(names_list)

    # set of all usernames we have a chat with
    read_matches = names & read

    # this has the rooms document for each group this user can join
    groups = driver.get_groups(names_list, username)
    # get the groups this user is part of 
    # used for 'read' colour change
    user_groups = driver.get_group_rooms(username)

    my_group_names = [room['groupname'] for room in user_groups]

    return render_template('matches.html', matches_list=matches, username=username, read=read_matches, group_list=groups, in_groups=my_group_names, match_category=match_category, blocklist=blocklist)


@app.route('/profile', methods=["GET", "POST"])
def profile():

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    if request.method == "POST":
        # update the profile
        form = request.form
        if 'bio' in form:
            driver.set_user_bio(user_id, form['bio'])
        if 'cluster-gran' in form:
            driver.set_user_cluster_granularity(user_id, int(form['cluster-gran']))

    # get this user bio and display it
    user_username = driver.get_user_username(user_id)
    user_bio = driver.get_user_bio(user_id)
    user_cluster_granularity = driver.get_user_cluster_granularity(user_id)

    # Check if the user has spotify integrated
    spotify_info = driver.find_one("spotify", {"user_id" : user_id})
    if spotify_info is not None:
        return render_template('profile.html', user_username=user_username, user_bio=user_bio, user_cluster_granularity=user_cluster_granularity, has_spotify="yes", artist_list=spotify_info["artists"])
    else:
        return render_template('profile.html', user_username=user_username, user_bio=user_bio, user_cluster_granularity=user_cluster_granularity)

@app.route('/user/<username>')
def user_profile(username):

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    user = driver.find_one("users", {"username" : username})

    userid = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    my_username = driver.get_username_from_userid(userid)

    if user['username'] == my_username:
        return redirect("/profile")


    if user:
        user_name = user['username']
        bio = user['bio']
        spotify = driver.find_one("spotify", {"user_id" : user['user_id']})
        has_spotify = spotify is not None
        artist_list = []

        if has_spotify:
            artist_list=spotify["artists"]

        return render_template("user.html", user_username=user_name, user_bio=bio, has_spotify=has_spotify, artist_list=artist_list)
    else:
        return render_template("userNotFound.html", chat_type="User")

@app.route('/group/<roomid>')
def group_page(roomid):

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    group = driver.find_one("rooms", {"roomid": roomid})

    if not group:
        # Group not found
        return render_template("userNotFound.html", chat_type="Group")

    users = group['users']
    groupname = group['groupname']

    return render_template("group.html", users=users, groupname = groupname)

@app.route('/block/<username>', methods=["GET", "POST"])
def block_user(username):

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")

    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    current_user = driver.get_username_from_userid(user_id)

    # block user 
    driver.add_to_blocklist(current_user, username)

    return redirect('/home')

@app.route('/delete', methods=["POST"])
def delete_account():

    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")
    
    redirect('/logout')
    
    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))
    usrname = driver.get_username_from_userid(user_id)
    addr = driver.get_email_with_cookie(request.cookies.get('session_id'))
    
    # Delete user's account
    driver.delete_user_account(usrname, addr, user_id)
    session.clear()
    
    return redirect('/login')

# === SOCKET FUNCTIONS ===

@socketio.on('join_room')
def handle_join_room_event(data):
    driver.add_user_to_room(data['room'], data['username'])
    app.logger.info("{} has joined chat room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])
    socketio.emit('public_join_room_announcement', data, broadcast=True)


@socketio.on('leave_room')
def handle_leave_room_event(data):
    room = driver.find_one('rooms', {'roomid': data['room']})
    if room['type'] == 'private':
        driver.delete_room(data['room'])
    else:
        driver.delete_user_from_room(data['room'], data['username'])
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])
    socketio.emit('public_leave_room_announcement', data, broadcast=True)


@socketio.on('send_message')
def handle_send_message(data):
    driver.send_message(data['room'], data['username'], data['message'])
    app.logger.info("{} has send message to room {}: {}".format(data['username'], data['room'], data['message']))
    socketio.emit('receive_message', data, room=data['room'])

@app.route('/spotify', methods=['POST'])
@cross_origin()
def store_top_artists():
    if not user_sanity_check():
        # Redirect user to login page
        return redirect("/login")
        
    response = jsonify(message="Simple server is running")
    data = request.json
    user_id = driver.get_user_id_with_cookie(request.cookies.get('session_id'))

    if driver.find_one('spotify', {"user_id": user_id}) is None:
        # insert new user        
        driver.insert_one('spotify', {'artists': data, "user_id" : user_id  })
    else:
        # existing user
        driver.update_one('spotify', {"user_id" : user_id}, {"$set": {'artists': data}})
    return redirect('/profile')

if __name__ == '__main__':
    socketio.run(app, debug=True)