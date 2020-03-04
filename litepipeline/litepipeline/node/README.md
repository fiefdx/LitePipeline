# Node

LitePipeline Node Service

# Run

```bash
# generate configuration file & scripts
mkdir ./litenode
cd ./litenode
# this will generate configuration.yml and other scripts
liteconfig -s node -o ./

# run manually
litenode -c ./configuration.yml or nohup litenode -c ./configuration.yml > /dev/null 2>&1 &

# install systemd service, user and group set to use which user and group to run litenode
sudo ./install_systemd_service.sh user group

# start
systemctl start litepipeline-node

# stop
systemctl stop litepipeline-node

# uninstall systemd service
sudo ./uninstall_systemd_service.sh
```
