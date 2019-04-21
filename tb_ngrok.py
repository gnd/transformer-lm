# This opens up a tunnel to see tensorboard on google colab via ngrok
# from https://medium.com/deep-learning-turkey/google-colab-free-gpu-tutorial-e113627b9f5d
import os
import subprocess

# You can change the directory name
LOG_DIR = 'logs'

subprocess.run(['wget', 'https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip'])
subprocess.run(['unzip', 'ngrok-stable-linux-amd64.zip']

get_ipython().system_raw(
    'tensorboard --logdir {} --host 0.0.0.0 --port 6006 &'
    .format(LOG_DIR))

get_ipython().system_raw('./ngrok http 6006 &')

subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'])
