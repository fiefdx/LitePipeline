#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

systemctl disable litepipeline-node
rm /lib/systemd/system/litepipeline-node.service
systemctl daemon-reload
echo "disable & remove litenode systemd service"
