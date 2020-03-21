# Viewer

LitePipeline Viewer Service

# Run

```bash
# generate configuration file & scripts
mkdir ./liteviewer
cd ./liteviewer
# this will generate configuration.yml and other scripts
liteconfig -s viewer -o ./

# run manually
liteviewer -c ./configuration.yml or nohup liteviewer -c ./configuration.yml > /dev/null 2>&1 &

# install systemd service, user and group set to use which user and group to run liteviewer
sudo ./install_systemd_service.sh user group

# start
systemctl start litepipeline-viewer

# stop
systemctl stop litepipeline-viewer

# uninstall systemd service
sudo ./uninstall_systemd_service.sh
```
