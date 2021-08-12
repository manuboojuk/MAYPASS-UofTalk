
from mongodriver import MongoDriver
from authenticator import Authenticator
import uuid
import random
import pickle
import numpy as np


if __name__ == '__main__':

    d = MongoDriver()
    a = Authenticator(d)

    password = "betaman1234"
    hashed_password = a._get_hash(password)
    
    models = {}

    for label in ['music', 'game', 'humor', 'movie', 'overall']:
        models[label] = {}
        for k in [3, 9, 15]:
            models[label][str(k)] = pickle.load(open(f"../trained-models/k-means-model-{label}-{k}.model", 'rb'))

    for i in range(15):

        bio = f"Hello, I am dummy user {i}."
        username = f"dummyuser{i}"
        email_id = f"user{i}.dummy@mail.utoronto.ca"
        code = a._get_verification_code()
        cookie = uuid.uuid4().hex

        entry = {
            "cookie": cookie, 
            "email_id": email_id,
            "password": hashed_password,
            "verification_code": code,
            "verified": True,
            "logged_in": False
        }

        # Insert the user to the authentication table
        d.insert_one('auth', entry)

        music = [random.randint(0, 4) for i in range(4)]
        movie = [random.randint(0, 4) for i in range(4)]
        game = [random.randint(0, 4) for i in range(4)]
        humour = [random.randint(0, 4) for i in range(6)]

        # Create a new user entry
        preferences = {
            "music": music,
            "movie": movie,
            "game": game,
            "humor": humour,
            "overall": music+game+movie+humour
        }

        cluster_association = {}
        for label in ['music', 'game', 'humor', 'movie', 'overall']:
            cluster_association[label] = {}        
            for k in [3, 9, 15]:
                cluster_association[label][str(k)] = int(models[label][str(k)].predict(np.asarray([preferences[label]]))[0])

        new_user_entry = {
            'user_id': uuid.uuid4().hex,
            'email': email_id,
            'username': username,
            'preferences': preferences,
            'cluster_association': cluster_association,
            'cluster_granularity' : random.choice([3, 9, 15]),
            'finished_survey': {"quest": True, "meme": True},
            'bio': bio
        }

        # Add this user to the users collection
        d.insert_one('users', new_user_entry)

        print("*"*15)
        print(f"Created dummyuser{i}")
        print(f"Cluster association: {cluster_association}")

    print("*"*15)