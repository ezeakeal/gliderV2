scp -i /home/dvagg/.ssh/id_rsa -r ~/Desktop/gliderV2/raspberry/* pi@$(sudo arp-scan --interface=eth0 --localnet | grep 10.42 | cut -f1):/opt/glider
