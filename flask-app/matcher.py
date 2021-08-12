from pymongo import MongoClient
import pickle
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from mongodriver import MongoDriver
from observer import Observer

class Matcher(Observer):

    def __init__(self, driver):
        self.driver = driver
        self.categories = ['music', 'game', 'humor', 'movie', 'overall']

    def act(self, user_id):
        """
        when we act we have to predict this 
        user using their new preferences
        """

        models = {}

        for label in self.categories:
            models[label] = {}
            for k in [3, 9, 15]:
                models[label][str(k)] = pickle.load(open(f"../trained-models/k-means-model-{label}-{k}.model", 'rb'))

        # use the models to predict which cluster this user belongs to
        cluster_association = {}
        for label in self.categories:
            vector = self.driver.fetch_preferences(user_id, "")
            cluster_association[label] = {}        
            for k in [3, 9, 15]:
                cluster_association[label][str(k)] = int(models[label][str(k)].predict(np.asarray([vector[label]]))[0])
            
        # update the cluster assoc now
        self.driver.update_user_association(user_id, cluster_association)

    def get_matches(self, user_id, category):
        """
        Given a user's id, return all their matches based on their granualarity choice
        """
        user = self.driver.find_one("users", {'user_id': user_id})

        if not user:
            print("user DNE")
            return

        granularity = user['cluster_granularity']
        association = user['cluster_association'][category][str(granularity)]
        matches = self.driver.find("users", {f"cluster_association.{category}.{granularity}" : association})

        matches = list(matches)
        matches.remove(self.driver.find("users", {'user_id': user_id})[0])

        return matches
