#For Manjaro/arch
mkdir log
sudo apt install tk xprintidle

#Create virtual env
python -m venv charts
source charts/bin/activate
pip3 install -r requirements.txt

