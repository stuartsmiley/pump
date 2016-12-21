# pump
Controlling the pump with python daemon 

## Running as a service
1. Copy pump.service to /lib/systemd/system/
2. sudo chmod 644 /lib/systemd/system/pump.service
3. sudo systemctl daemon-reload
4. sudo systemctl enable pump.service

* sudo systemctl stop application.service
* sudo systemctl start application.service
* sudo systemctl restart application.service
* sudo systemctl status application.service
