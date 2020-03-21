#!/bin/bash
cmd_path=$(dirname $0)
cd $cmd_path

systemctl disable litepipeline-viewer
rm /lib/systemd/system/litepipeline-viewer.service
systemctl daemon-reload
echo "disable & remove liteviewer systemd service"
