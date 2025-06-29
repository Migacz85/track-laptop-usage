#For Manjaro/arch
mkdir log
sudo apt install tk xprintidle xdotool
sudo apt install yay
sudo apt install hciconfig

sudo pip3 install face-recognition

#Create virtual env
python -m venv charts
source charts/bin/activate
pip3 install -r requirements.txt 

