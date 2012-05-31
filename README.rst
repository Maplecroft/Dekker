Dekker: simple HTTP API on PostGIS
==================================

Dekker is very simple a Flask-based HTTP API for getting point-value and
point-buffer data from raster files stored in a PostGIS 2 database.


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

Assuming it is deployed at dekker.example.com, you can then request, eg::

    $ curl  -H "Content-type: application/json" \
    > "http://dekker.example.com/point?lon=51&lat=-2&tif%5b%5d=source_file_1.tif&tif%5b%5d=source_file_2.tif"
    {
      "count": 2,
      "list": [
        {
          "lat": "-2",
          "lon": "51",
          "value": 1.2345,
          "view": "source_file_1.tif"
        },
        {
          "lat": "-2",
          "lon": "51",
          "value": 5.4321,
          "view": "source_file_2.tif"
        }
      ],
      "time": 0.073075
    }

For points, and::

    $ curl  -H "Content-type: application/json" \
    > "http://dekker.example.com/buffer?radius=10&lon=51&lat=-2&tif%5b%5d=source_file_1.tif&tif%5b%5d=source_file_2.tif"
    {
      "count": 2,
      "list": [
        {
          "lat": -2.00000,
          "tif": "source_file_1.tif",
          "gid": 0,
          "lon": 51.00000,
          "value": 3.5000000
        },
        {
          "lat": -2.00000,
          "tif": "source_file_2.tif",
          "gid": 0,
          "lon": 51.00000,
          "value": 10.0000000
        }
      ],
      "time": 2.119631
    }

for buffers.
