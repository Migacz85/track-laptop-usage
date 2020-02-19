#For Manjaro/arch
mkdir log
sudo pacman -S  tk xprintidle xdotool
sudo pacman -S yay
yay hciconfig

sudo pip3 install face-recognition

#Create virtual env
python -m venv charts
source charts/bin/activate
pip3 install -r requirements.txt 

