#!/bin/bash

echo "Install basic dependencies"
sudo apt-get update
sudo apt-get install vim -y

echo "Install AppRecommender dependencies"
cd /vagrant
./install_dependencies.sh

echo "Prepare AppRecommender data"
cd /vagrant/src/bin
./apprec.py --init
./apprec.py --train
