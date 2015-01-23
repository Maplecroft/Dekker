# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  # Using a blank Ubuntu 14.04 box
  config.vm.box = "fgrehm/trusty64-lxc"
  config.vm.box_url = "https://vagrantcloud.com/fgrehm/boxes/trusty64-lxc"

  # Mounting the app files and salt states
  config.vm.synced_folder "salt/roots/", "/srv/salt/"
  config.vm.synced_folder ".", "/mnt/bootstrap"

  # Provision box with masterless salt
  config.vm.provision :salt do |salt|
    salt.minion_config = "salt/minion.conf"
    salt.run_highstate = true
    salt.verbose = true  # Set to true for debugging
  end
end
