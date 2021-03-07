# %%
import numpy as np
import matplotlib.pyplot as plt
from utils import *
import importlib
from scipy.linalg import expm
from tqdm import tqdm_notebook
import transform
import sensors
import landmark_map
import kalman_filter
importlib.reload(transform)
importlib.reload(sensors)
importlib.reload(landmark_map)
importlib.reload(kalman_filter)

from transform import Transform
from sensors import IMU, StereoCamera
from landmark_map import LandmarkMap
from kalman_filter import KalmanFilter
# %%
filename = "./data/10.npz"
t,features,linear_velocity,angular_velocity,K,b,imu_T_cam = load_data(filename, load_features = True)

# downsample features
features = features[:,::20,:]

#%%
stero_cam = StereoCamera(K,b,features)
tf = Transform()
imu = IMU(t, linear_velocity, angular_velocity)

# %%
pose_all = np.zeros([4,4,imu.get_length()])
pose_all[:,:,0] = Transform.calcualte_pose(np.eye(3),np.zeros(3))

for idx in range(imu.get_length()-1):
    v = imu.linear_velocity[:,idx]
    omega = imu.angular_velocity[:,idx]
    twist = Transform.calculate_twist(np.concatenate([v,omega]))
    pose_all[:,:,idx+1] = pose_all[:,:,idx] @ expm(imu.delta_t * twist)
# %%
visualize_trajectory_2d(pose_all,show_ori=True)

# %% run loop for update-
# data_length = t.shape[1]
kf = KalmanFilter()
data_length = t.shape[1]
myMap = LandmarkMap(stero_cam.n_features)

for idx in tqdm_notebook(range(data_length)):
    robot_pose = pose_all[:,:,idx]

    # separate observed landmarks. old: landmk seen before, new: unseen landmk
    landmark_idx = stero_cam.get_landmark_seen(idx) # all landmarks in current frame
    old_landmk, new_landmk = myMap.get_old_new_landmarks(landmark_idx)

    # initialize new landmarks
    if len(new_landmk) > 0:
        pixel_new = stero_cam.get_landmark_freatures(new_landmk, idx)
        xyz_optical = stero_cam.pixel_to_xyz(pixel_new, max_depth=50)
        xyz_world = tf.optical_to_world(robot_pose, xyz_optical) # in homogenous
        myMap.init_landmarks(new_landmk,xyz_world[:3])

    # update old landmarks using EKF
    if len(old_landmk) > 0:
        pixel_old = stero_cam.get_landmark_freatures(old_landmk, idx)
        landmk_xyz = myMap.get_landmarks(old_landmk)
        jacobian = kf.calculate_observation_jacobian(stero_cam,tf,robot_pose,old_landmk,myMap)
        K_gain = kf.calculate_kalman_gain(myMap.cov,jacobian,stero_cam.cov)
        myMap.update_landmarks(stero_cam,tf,robot_pose,landmk_xyz,pixel_old,K_gain)
        myMap.update_cov(K_gain,jacobian)
# %%
myMap.plot_map()
# %%