# Manager

LitePipeline Manager Service

# Run

```bash
# generate configuration file & scripts
mkdir ./litemanager
cd ./litemanager
# this will generate configuration.yml and other scripts
liteconfig -s manager -o ./

# run manually
litemanager -c ./configuration.yml or nohup litemanager -c ./configuration.yml > /dev/null 2>&1 &

# install systemd service, user and group set to use which user and group to run litemanager
sudo ./install_systemd_service.sh user group

# start
systemctl start litepipeline-manager

# stop
systemctl stop litepipeline-manager

# uninstall systemd service
sudo ./uninstall_systemd_service.sh
```
