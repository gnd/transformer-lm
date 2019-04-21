#!/bin/sh
# This opens up a tunnel to see tensorboard on google colab via ngrok
# from on https://medium.com/deep-learning-turkey/google-colab-free-gpu-tutorial-e113627b9f5d

LOG_DIR='/content/drive/My Drive/ai-work/logs/'

# remove old ngrok
if [ -e ngrok-stable-linux-amd64.zip ]; then
    rm ngrok-stable-linux-amd64.zip
    rm ngrok
fi

# get the new ngrok, unzip & run everything
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
unzip ngrok-stable-linux-amd64.zip
tensorboard --logdir "$LOG_DIR" --host 0.0.0.0 --port 6006 &
sleep 2
./ngrok http 6006 &
sleep 2
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
