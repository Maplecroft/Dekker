# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # Using a blank Ubuntu 14.04 lxc container
  config.vm.box = "fgrehm/trusty64-lxc"

  # Download URL for the container
  config.vm.box_url = "https://vagrantcloud.com/fgrehm/boxes/trusty64-lxc"

  # Mount the salt roots/pillar folders so that they can all be served by salt
  config.vm.synced_folder ".", "/srv/www/dekker"

  # Port forwarding for dekker service
  config.vm.network :forwarded_port, guest: 80, host: 8080

  # Set up masterless salt on the box with the salt provisioner
  config.vm.provision :salt do |salt|

    # Let the salt provisioner to its thing and add the minion config file
    salt.minion_config = "salt/minion"

    # We don't want to run state.highstate, we will manually call highstate
    # with the shell later to we can pass in our env=dev argument
    salt.run_highstate = false

    # Set salt.install to git so we can explicitly say which version to install
    # Default installs latest but it's better to be in control of any upgrades
    salt.install_type = "git"
    salt.install_args = "v2014.7.1"

  end

  # Use the shell provisioner to run `salt-call` to install our deps
  config.vm.provision :shell do |shell|

    # Stop vagrant from replacing the stdout colours
    shell.keep_color = true

    # The `env=dev` argument tells salt that we want to use our
    # developer environment
    shell.inline = "sudo salt-call --config-dir=$1 state.highstate pillar=$2 saltenv=$3"
    shell.args = [
        "/srv/www/dekker/salt/",
        "{'db_password':'vagrant','password':'dekker'}",
        "dev"
    ]

  end

end
