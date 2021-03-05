import numpy as np
import matplotlib.pyplot as plt

class LandmarkMap:
    def __init__(self,n_landmark):
        self.n_landmark = n_landmark
        self.landmarks = np.zeros([4,self.n_landmark])

    def plot_map(self):
        plt.scatter(self.landmarks[0], self.landmarks[1], 1)