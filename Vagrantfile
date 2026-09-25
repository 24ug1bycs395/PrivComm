# -*- mode: ruby -*-
# vi: set ft=ruby :

# Tuned 3-Node strongSwan IPsec VPN Testbed (Fast & Lightweight)
# VirtualBox Host-Only Network (192.168.56.0/24)

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04" # Lightweight, fast boot base box

  # Global VM provider settings
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "512"
    vb.cpus = 1
    vb.gui = false
    vb.linked_clone = true   # ⚡ Instant disk creation & 80% less disk space
  end

  # ==========================================
  # VM 1: Initiator (Client / VPN Gateway A)
  # ==========================================
  config.vm.define "vm1-initiator" do |vm1|
    vm1.vm.hostname = "vm1-initiator"
    vm1.vm.network "private_network", ip: "192.168.56.10"
    vm1.vm.provision "shell", inline: <<-SHELL
      echo ">>> Provisioning VM1 (Initiator)..."
      sudo apt-get update -qq
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        strongswan strongswan-swanctl strongswan-pki libcharon-extra-plugins curl iperf3 tcpdump
      # Allow password/key ssh authentication
      sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
      sudo systemctl restart ssh
      echo "vm1-initiator ready!"
    SHELL
  end

  # ==========================================
  # VM 2: Responder (Server / VPN Gateway B)
  # ==========================================
  config.vm.define "vm2-responder" do |vm2|
    vm2.vm.hostname = "vm2-responder"
    vm2.vm.network "private_network", ip: "192.168.56.20"
    vm2.vm.provision "shell", inline: <<-SHELL
      echo ">>> Provisioning VM2 (Responder)..."
      sudo apt-get update -qq
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        strongswan strongswan-swanctl strongswan-pki libcharon-extra-plugins curl iperf3 tcpdump nginx
      sudo systemctl restart ssh
      echo "vm2-responder ready!"
    SHELL
  end

  # ==========================================
  # VM 3: Observer / Network Sniffer
  # ==========================================
  config.vm.define "vm3-observer" do |vm3|
    vm3.vm.hostname = "vm3-observer"
    vm3.vm.network "private_network", ip: "192.168.56.30", nic_promisc: "allow-all"
    vm3.vm.provision "shell", inline: <<-SHELL
      echo ">>> Provisioning VM3 (Observer)..."
      sudo apt-get update -qq
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tshark tcpdump libpcap-dev
      # Allow non-root packet capture
      sudo chmod +x /usr/bin/dumpcap || true
      sudo systemctl restart ssh
      echo "vm3-observer ready!"
    SHELL
  end
end
