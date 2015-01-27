#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import argparse
import os

import conf


def prepare_table():
    """Sets up the table in the database"""

    # Bit stupid, but we want all the rasters in one table (?)
    # So mkdir a directory so that the raster2pgsql is happy (it
    # thinks that is a raster, so it will make a table correctly.)
    # Bit odd, and probably the wrong way to do it....
    cmd = "mkdir %s; raster2pgsql -p -I -F %s | psql %s; rmdir %s" % (
        conf.TABLE, conf.TABLE, conf.DBNAME, conf.TABLE)
    print cmd
    os.system(cmd)


def load_rasters_from_dir(dirname):
    """Take all the tif files and load them."""
    for fn in os.listdir(dirname):
        cmd = "raster2pgsql -s %s -a -M -F -t 64x64 %s %s | psql %s" % (
            conf.SRID,
            os.path.join(dirname, fn),
            conf.TABLE,
            conf.DBNAME,
        )
        print cmd
        os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description='Prepare and load rasters')
    parser.add_argument('--prepare', dest='prepare', action='store_true',
                        default=False,
                        help='Create the table')
    parser.add_argument('--dirname', dest='dirname', action='store',
                        default=False,
                        help='Load rasters from dir <dirname>')

    args = parser.parse_args()
    if args.prepare:
        prepare_table()
    if args.dirname:
        load_rasters_from_dir(args.dirname)
    if not args.prepare and not args.dirname:
        parser.print_help()


if __name__ == '__main__':
    main()
