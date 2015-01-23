# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "fgrehm/trusty64-lxc"
  config.vm.box_url = "https://vagrantcloud.com/fgrehm/boxes/trusty64-lxc"

  config.vm.synced_folder "salt/roots/", "/srv/salt/"
  config.vm.synced_folder ".", "/mnt/bootstrap"

  config.vm.provision :salt do |salt|
    salt.minion_config = "salt/minion.conf"
    salt.run_highstate = true
    salt.verbose = true
  end
end
