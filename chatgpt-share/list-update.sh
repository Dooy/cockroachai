#!/bin/bash
set -e

git clone https://github.com/frontend-winter/sharelist.git sharelist
cd sharelist
git pull
mv dist ../list
cd ..
chmod -R 755 list
rm -rf sharelist