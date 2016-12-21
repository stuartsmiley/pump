# pump
Controlling the pump with python daemon 

## Running as a service
Copy pump.service to /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pump.service

sudo systemctl stop application.service
sudo systemctl start application.service
sudo systemctl restart application.service
sudo systemctl status application.service
