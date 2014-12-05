# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT
echo I am provisioning...
date > /etc/vagrant_provisioned_at
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.provider "virtualbox" do |v|
    v.memory = 512
    v.cpus = 1
  end

  config.vm.provision "shell", inline: $script
end

Vagrant::Config.run do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.network :bridged

  config.vm.share_folder "bootstrap", "/mnt/bootstrap", ".", :create => true
  config.vm.provision :shell, :path => ".shell/dekker.sh"
  
  # PostgreSQL Server port forwarding
  config.vm.forward_port 5432, 15432

end
