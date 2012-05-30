Deployment with Runit and Nginx
===============================

`Runit <http://smarden.org/runit/>`_ is perfect for running an app like this.
There are great docs elsewhere for installing and setting up runit, but here is
an example config for this app::

    #!/bin/sh

    GUNICORN=/path/to/fpr/virtualenv/bin/gunicorn
    ROOT=/path/to/flask-postgis-rasters
    PID=/var/run/gunicorn-fpr.pid

    APP=app:app

    if [ -f $PID ]; then rm $PID; fi

    cd $ROOT
    exec $GUNICORN --pid=$PID $APP --workers=4 -b localhost:8000

It's advisable to run this as a user other than root, but you can do that
easily with runit by changing the ownership of the ``ok``, ``control``, and
``status`` files inside the ``supervise`` sub-directory of the service to the user
you want to run the service as, then just calling ``sv start fpr`` as that user.

Given the above setup with Runit, the required Nginx configuration is quite
simple::

    upstream fpr
    {
        server localhost:8000;
    }

    server
    {
        listen 80;
        server_name fpr.example.com;
        root /path/to/flask-postgis-rasters;

        location /
        {
            proxy_pass http://fpr;
        }
    }

