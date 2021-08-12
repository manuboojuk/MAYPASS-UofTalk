from pymongo import MongoClient
from observer import Observable
from datetime import datetime
import uuid

class MongoDriver(Observable):
    """
    THIS CLASS IS FOR ANY INTERACTIONS WITH THE DATABASE

    client: MongoClient
    db: the database
    user_col: the column of users
    authentication_col: the column of authenticated users
    rooms: the collection of all rooms/members
    messages: the collection of all messages

    directory: dictionary storing the associated collections with the keywords

    """

    def __init__(self):
        super().__init__()
        self.client = MongoClient("removed_for_privacy")
        self.db = self.client['UofTalk']
        self.user_col = self.db['users']
        self.authentication_col = self.db['authentication']
        self.rooms = self.db['rooms']
        self.messages = self.db['messages']
        self.spotify = self.db['spotify']

        
        self.directory = {'users': self.user_col, 'auth': self.authentication_col, 'rooms': self.rooms, 'messages': self.messages, 'spotify' : self.spotify}

    def find(self, table, query):
        return self.directory[table].find(query)

    def find_one(self, table, query):
        return self.directory[table].find_one(query)

    def insert_one(self, table, entry):
        return self.directory[table].insert_one(entry)

    def update_one(self, table, query, new_value):
        return self.directory[table].find_one_and_update(query, new_value)

    def get_user(self, user_id):
        """
        Return user iff user with <user_id> exists in the database
        Return none otherwise
        """
        return self.user_col.find_one({"user_id": user_id})

    def get_username_from_userid(self, user_id):
        user_id =  self.user_col.find_one({"user_id": user_id})
        return user_id['username']

    def update_preferences(self, user_id, category, new_vector):
        """
        update the preferences of user <user_id>  to <new_vector>
            This function will only change the <category> preferences vector
        
        This function will also update the overall vector as well

        return True on succsess, False on failure

        NOTE: 
        user_id must be int
        category must be string
        new_vector must be a python list of floats or ints
        """
        # check if user exists
        if not self.get_user(user_id):
            return False

        # find the user with given id
        query = {"user_id" : user_id}
        # set the category vector to the new vector
        new_value = {"$set": {f"preferences.{category}" : new_vector}}
        
        # apply changes
        self.user_col.update_one(query, new_value)

        # we now need to update the overall vector
        old_preferences = self.fetch_preferences(user_id, "")

        # get all the values and concat them
        new_overall = []
        for key in ['music', 'game', 'movie', 'humor']:
            new_overall += old_preferences[key]

        new_value = {"$set": {"preferences.overall" : new_overall}}
        self.user_col.update_one(query, new_value)

        #NOTE: retrain models to work with correct number of dimensions
        # tell the matcher to reassign the cluster assoc
        self.notify(user_id)

        return True

    def fetch_preferences(self, user_id, category):
        """
        Return the preferences as a dictionary
        will return preferences.category 
        if category is the empty string, will return all preferences
        
        Will return None if no user is found

        user_id: int 
        category: str
        get_all: bool
        """
        user = self.get_user(user_id)
        if user:
            if category != "":
                return user["preferences"][category]
            return user["preferences"]

    def update_user_association(self, user_id, new_assoc):
        """
        Update the cluser assoc for this category and this k value
        
        new_assoc: dictionary
            label: {k: cluster}
        """
        query = {"user_id" : user_id}
        field = "cluster_association"
        new_value = new_value = {"$set": {field : new_assoc}}
        self.user_col.update_one(query, new_value)

    def get_user_bio(self, user_id):
        """
        Get the bio of this user and return it as text
        """
        user = self.get_user(user_id)
        if user:
            return user['bio']
        return None

    def get_user_username(self, user_id):
        """
        Get the username of this user and return it as text
        """
        user = self.get_user(user_id)
        if user:
            return user['username']
        return None

    def get_user_cluster_granularity(self, user_id):
        """
        Get the cluster granularity of this user and return it as text
        """
        user = self.get_user(user_id)
        if user:
            return user['cluster_granularity']
        return None

    def set_user_bio(self, user_id, new_bio):
        query = {"user_id": user_id}
        new_value = {"$set": {"bio": new_bio}}
        self.user_col.update_one(query, new_value)

    def set_user_cluster_granularity(self, user_id, new_val):
        query = {"user_id": user_id}
        new_value = {"$set": {"cluster_granularity": new_val}}
        self.user_col.update_one(query, new_value)


    def get_email_with_cookie(self, cookie):
        """
        Query the database with the given cookie id to find the user's email that the cookie is associated with
        """
        user = self.authentication_col.find_one({"cookie": cookie})
        if user is not None:
            return user['email_id']

    def get_cookie_with_email(self, email):
        """
        Query the database with the given an email to find the user's cookie associated with them
        """
        user = self.authentication_col.find_one({"email_id": email})
        if user is not None:
            return user['cookie']

    def get_user_id_with_cookie(self, cookie):
        """
        Query the database with the given cookie id to find the user id 
        """
        email = self.get_email_with_cookie(cookie)
        if email:
            return self.user_col.find_one({"email": email})['user_id']

    def is_user_verified(self, email):
        """
        Query the database to check if the user with the given email verified their email
        """
        user = self.authentication_col.find_one({"email_id": email})
        return user['verified']

    def get_authentication_table(self):
        return self.authentication_col

    def is_user_finished_survey(self, user_id):
        user = self.user_col.find_one({"user_id": user_id})
        if user:
            return user['finished_survey']['meme'] and user['finished_survey']['quest']

    def is_user_finished_survey_status(self, user_id):
        user = self.user_col.find_one({"user_id": user_id})
        if user:
            return user['finished_survey']

    def set_user_finished_survey(self, user_id, survey_type):
        query = {"user_id": user_id}
        new_value = {"$set": {f"finished_survey.{survey_type}": True}}
        self.user_col.update_one(query, new_value)
    
    def delete_user_account(self, usrname, addr, user_id):
        """
        Given the user's username <usrname>, email address <addr> and user_id <user_id>, delete the user's 
        account and information from all collections in database.
        """
        query_id = {"user_id": user_id}
        query_email_id = {"email_id": addr}
        query_email = {"email": addr}
        query_pm = {"users": {"$in": [usrname]}, "type": "private"}
        query_group = {"users": {"$in": [usrname]}, "type": "group"}
        
        self.directory['users'].delete_one(query_id)
        self.directory['spotify'].delete_one(query_id)
        self.directory['auth'].delete_one(query_email_id)
        
        private_rooms = self.directory['rooms'].find(query_pm)
        group_chats = self.directory['rooms'].find(query_group)
        
        for room in private_rooms:
            self.delete_room(room["roomid"])
        
        for room in group_chats:
            self.delete_user_from_room(room["roomid"], usrname)
            # For sanity check.
            if room["users"] == []:
                self.delete_room(room["roomid"])

    def __str__(self):
        return "Driver for interacting mongoDB"

    def __repr__(self):
        return self.__str__()

    # === CHAT METHODS ===

    def create_new_private_room(self, users):
        """
        Generate a unique roomid and create a new PRIVATE ROOM with <users>"
        """
        roomid = uuid.uuid4().hex
        self.rooms.insert_one({'roomid': roomid, 'users': users, 'type': 'private','messages': []})
        return roomid

    def create_new_group_room(self, groupname, users):
        """
        Generate a unique roomid and create a new GROUP with <groupname> and <users>"
        """
        roomid = uuid.uuid4().hex
        self.rooms.insert_one({'roomid': roomid, 'groupname': groupname, 'status': 'open', 'users': users, 'type': 'group','messages': []})
        return roomid

    def delete_room(self, roomid):
        """
        Delete roomid from DB
        """
        self.rooms.delete_one({'roomid': roomid})

    def add_user_to_room(self, roomid, username):
        """
        ADDS username to the list of users in the room with the given roomid
        """
        room = self.rooms.find_one({'roomid': roomid})
        if room is not None:
            users = room['users']
            if username not in users: users.append(username)
            self.rooms.update_one({'roomid': roomid},  {'$set': {'users': users}})

    def delete_user_from_room(self, roomid, username):
        """
        DELETES username from the list of users in the room with given roomid
        """
        room = self.rooms.find_one({'roomid': roomid})
        users = room['users']
        users.remove(username)
        if users == []:
            self.rooms.delete_one({'roomid': roomid})
        else:
            self.rooms.update_one({'roomid': roomid}, {'$set': {'users': users}})

    def get_active_private_rooms(self, userid):
        """
        Return a list of all active PRIVATE chat rooms for <userid> along with the username of the other member.
        """
        username = self.get_username_from_userid(userid)
        rooms = {}
        blocklist = self.get_blocklist(username)
        
        for room in self.rooms.find():
            if any(x in blocklist for x in room['users']):
                continue
            if username in room['users'] and room['type'] == 'private' :
                room['users'].remove(username)
                other_user = room['users'][0]
                rooms[room['roomid']] =  other_user
        return rooms

    def get_active_group_rooms(self, userid):
        """
        Return a list of all active GROUP chat rooms for <userid> along with an assigned room name.
        """
        username = self.get_username_from_userid(userid)
        rooms = {}
        for room in self.rooms.find():
            if username in room['users'] and room['type'] == 'group':
                room['users'].remove(username)
                rooms[room['roomid']] =  {'groupname': room['groupname'], 'users': room['users']}
        return rooms

    def get_users_from_room(self, roomid):
        """
        Returns a list of all Users in the specified room with roomid.
        """
        room_users = []
        for room in self.rooms.find({'roomid': roomid}):
            for user in room['users']:
                room_users.append(user)
        return room_users
        
    def send_message(self, roomid, username, message):
        """
        Handles storing messages in db.
        """
        room = self.rooms.find_one({'roomid': roomid})
        messages = room['messages']

        message = {
                "sender": username,
                "message": message,
                "timestamp": datetime.today(),
            }
        messages.append(message)
        self.rooms.update_one({'roomid': roomid}, {'$set': {'messages': messages}})

    def get_messages(self, roomid):
        """
        Handles retrieving past conversations from db along with users who sent them.
        """
        #users, msgs = [], []
        msgs = []

        room = self.rooms.find_one({'roomid': roomid})
        if room is not None:
            return room['messages']

    def get_roomid_from_users(self, type, users):
        """
        Given the room type, and a list of users, return the respective roomid.
        """
        rooms_of_type = self.rooms.find({'type': type})
        room_id = None
        for room in rooms_of_type:
            counter = 0
            for user in room['users']:
                if user in users:
                    counter += 1
            if counter == len(room['users']):
                room_id = room['roomid']
        return room_id

    def update_group_privacy(self, roomid, status):
        print(roomid)
        if roomid is not None:
            self.rooms.update_one({'roomid': roomid}, {'$set': {'status': status}})

    def get_room_type(self, roomid):
        """Given roomid, return room type (private or group)"""
        if roomid is not None:
            return self.rooms.find_one({'roomid': roomid})['type']
    
    def get_group_name_from_roomid(self, roomid):
        """Given roomid, return group name"""
        return self.rooms.find_one({'roomid': roomid})['groupname']

    def get_room(self, roomid):
        """ Given roomid, return the group object"""
        return self.rooms.find_one({})

    def get_group_rooms(self, username):
        """
        Given <username> get all the group rooms this user is part of
        """

        return self.rooms.find({"$and" : [{"users": username}, {"type": "group"}]})

    def get_groups(self, username_list, username):
        """
        Given a list of usernames, find all groups with them in it
        """
        open_groups = {"$and" : [{"type": "group"},{"status": "open"},{"users": {"$in": username_list}}]}

        my_groups = {"$and" : [{"type": "group"},{"users": username}]}

        return self.rooms.find({"$or" : [open_groups, my_groups]})

    def add_to_blocklist(self, username, blocked_user):
        """
        Adds a user to a blocklist
        """

        # get blocklist 
        blocklist = self.get_blocklist(username)


        if blocked_user not in blocklist:
            blocklist.append(blocked_user)
            self.user_col.update_one({'username': username}, {'$set': {'blocklist': blocklist}})

    def get_blocklist(self, username):
        user = self.user_col.find_one({'username': username})
        return user['blocklist']
