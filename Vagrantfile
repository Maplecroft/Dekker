# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # Using a blank Ubuntu 14.04 lxc container
  config.vm.box = "fgrehm/trusty64-lxc"

  # Download URL for the container
  config.vm.box_url = "https://vagrantcloud.com/fgrehm/boxes/trusty64-lxc"

  # Provision box with masterless salt
  config.vm.provision :salt do |salt|

    # Set the location of the minion config, this is the relative path
    # on the host machine, not the guest
    salt.minion_config = "salt/minion.conf"

    # This runs state.highstate on provisioning which installs packages,
    # services, etc if they are not present on the VM but are listed in
    # the state files
    salt.run_highstate = true

    # Set salt.install to git so we can explicitly say which version to install
    # Default installs latest but it's better to be in control of any upgrades
    salt.install_type = "git"
    salt.install_args = "v2014.7.1"

    # This outputs debug data to the console, for testing purposes.
    # Set this to false when not needed.
    salt.verbose = true
  end
end
