import numpy as np
from sklearn.cluster import KMeans
import pickle
import random 

def generate_data(n):

    print("Generating data...")

    # Generate n random data points
    datasets = {"music": [], "movie": [], "game": [], "humor":[], "overall": []}
    for i in range(n):

        # Create vectors
        music = [random.randint(0, 4) for i in range(4)]
        movie = [random.randint(0, 4) for i in range(4)]
        game = [random.randint(0, 4) for i in range(4)]
        humor = [random.randint(0, 4) for i in range(6)]
        overall = music+game+movie+humor

        datasets["music"].append(music)
        datasets["movie"].append(movie)
        datasets["game"].append(game)
        datasets["humor"].append(humor)
        datasets["overall"].append(overall)

    print(f"Created {i+1} datapoints.")

    for key in datasets:
        print(f"Created {key}.npy dataset")
        np.save(f"datasets/{key}.npy", np.array(datasets[key]))

    print("Done.")


def train_models():

    for label in ['music', 'game', 'humor', 'movie', 'overall']:

        X = np.load(f"datasets/{label}.npy", allow_pickle=True)

        for k in [3, 9, 15]:

            clustering = KMeans(n_clusters=k, random_state=5)
            clustering.fit(X)
            
            pickle.dump(clustering, open(f"../trained-models/k-means-model-{label}-{k}.model", 'wb'))
            print(f"Created model. Label:{label} K={k}")

    
if __name__ == '__main__':
    # generate_data(5000)
    train_models()