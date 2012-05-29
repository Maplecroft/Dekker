#!/usr/bin/env python 
# -*- coding: iso-8859-15 -*-
import argparse
import os

import conf


def prepare_table():
    """Sets up the table in the database"""
    cmd = "raster2pgsql -p -I -F %s | psql %s" % (conf.TABLE, conf.DBNAME)
    os.system(cmd)


def load_rasters_from_dir(dirname):
    """Take all the tif files and load them."""
    for fn in os.listdir(dirname):
        cmd = "raster2pgsql -a -M -F -t 64x64 %s %s | psql %s" % (
            os.path.join(dirname, fn),
            conf.TABLE,
            conf.DBNAME)
        print cmd
#        os.system(cmd)


