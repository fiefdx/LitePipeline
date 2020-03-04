#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

systemctl disable litepipeline-manager
rm /lib/systemd/system/litepipeline-manager.service
systemctl daemon-reload
echo "disable & remove litemanager systemd service"
