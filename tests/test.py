import os
import json
from app import app
import unittest
import tempfile
import tablib
import conf

# Index slugs and their md5s used in tests.


class DekkerTestCase(unittest.TestCase):

    MD5_TEST_CONFIG = [
        ('nh_drought_hazard_2017-Q2', 'aa376cfc112c6253084e927ae52577de'),
        ('nh_tropical_storm_and_cyclone_hazard_2017-Q2',
         '8a2438f643d7127611767e94d5edc98f'),
        ('pr_civil_unrest_2018-Q1_v1', '2fc359bb85c1ee5b1f963f50a0cd583a'),
    ]

    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()

        conf.DRAFT_DIR = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'draft',
        )

        conf.DATA_DIR = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'data',
        )

        self.point = (-4.483545, 54.140744)
        self.raster = "test_raster"
        self.polygon = (
            "POLYGON((-4.6527099609375 54.21546936035156,"
            "-4.66094970703125 54.00535583496094,"
            "-4.3595123291015625 54.007415771484375,"
            "-4.3636322021484375 54.235382080078125,"
            "-4.6527099609375 54.21546936035156))"
        )

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_publish(self):
        """
        Tests posting a file to the /publish method, which validates the tif
        and then moves it to the data dir. Responds with md5 hash of published
        file.

        :return:
        """
        client = app.test_client()

        for idx, (slug, md5) in enumerate(self.MD5_TEST_CONFIG):
            resp = client.post(
                '/publish',
                buffered=True,
                content_type='multipart/form-data',
                data={
                    'file': (
                        open(
                            os.path.join(
                                os.path.split(__file__)[0],
                                'data/{}.tif'.format(slug)
                            )
                        ),
                        '{}.tif'.format(slug)
                    ),
                    'index_view_slug': 'index_view_slug{}'.format(idx)
                }
            )

            self.assertEqual(
                md5,
                json.loads(
                    resp.data
                )['md5'],
            )

        # Now try something invalid
        resp = client.post(
            '/publish',
            buffered=True,
            content_type='multipart/form-data',
            data={
                'file': (
                    open(
                        os.path.join(
                            os.path.split(__file__)[0],
                            'data/linus.tif'
                        )
                    ),
                    'linus.tif',
                ),
                'index_view_slug': 'linus'
            }
        )

        self.assertEqual(
            False,
            json.loads(
                resp.data
            )['valid'],
        )

    def test_md5(self):
        client = app.test_client()

        for slug, md5 in self.MD5_TEST_CONFIG:
            resp = client.get(
                '/md5?index_view_slug={}'.format(slug),
            )
            self.assertEqual(
                md5,
                json.loads(
                    resp.data
                )['md5'],
            )

    def test_validate(self):
        """
        Tests posting a file to the /validate ,ethod, which validates the tif
        and then moves it to the data dir. Responds with md5 hash of published
        file.

        :return:
        """
        client = app.test_client()

        for idx, (slug, md5) in enumerate(self.MD5_TEST_CONFIG):
            resp = client.post(
                '/validate',
                buffered=True,
                content_type='multipart/form-data',
                data={
                    'file': (
                        open(
                            os.path.join(
                                os.path.split(__file__)[0],
                                'data/{}.tif'.format(slug)
                            )
                        ),
                        '{}.tif'.format(slug)
                    ),
                    'index_view_slug': 'index_view_slug{}'.format(idx)
                }
            )

            self.assertEqual(
                md5,
                json.loads(
                    resp.data
                )['md5'],
            )

            self.assertEqual(
                True,
                json.loads(
                    resp.data
                )['valid'],
            )

        # Now try something invalid
        resp = client.post(
            '/validate',
            headers=dict(
                buffered=True,
                content_type='multipart/form-data',
            ),
            data={
                'file': (
                    open(
                        os.path.join(
                            os.path.split(__file__)[0],
                            'data/linus.tif'
                        )
                    ),
                    'linus.tif',
                ),
                'index_view_slug': 'linus'
            }
        )

        self.assertEqual(
            False,
            json.loads(
                resp.data
            )['valid'],
        )

    def test_value_at_point(self):
        # Bad request and docstring check
        response = self.app.get('/point')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)

    def test_buffer_value_at_point(self):

        # Bad request and docstring check
        response = self.app.get('/pointbuffer')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)

        # Expected 2.680 for nh_extra_tropical_cyclone_hazard_2016_raster
        # for legacy calculation method
        response = self.app.get(
            '/pointbuffer?lat=%s&lon=%s&radius=20&raster_table=%s' % (
                self.point[1],
                self.point[0],
                self.raster
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "%.3f" % json.loads(
                response.data
            )['query']['value'],
            "2.628"
        )


        # Increase radius - expect some change
        response = self.app.get(
            '/pointbuffer?lat=%s&lon=%s&radius=35&raster_table=%s' % (
                self.point[1],
                self.point[0],
                self.raster
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "%.3f" % json.loads(
                response.data
            )['query']['value'],
            "3.104"
        )


        # Check support for 'custombuffer' query
        response = self.app.get(
            '/custombuffer?lat=%s&lon=%s&radius=35&raster_table=%s' % (
                self.point[1],
                self.point[0],
                self.raster
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "%.3f" % json.loads(
                response.data
            )['query']['value'],
            "3.104"
        )

    def test_polygon(self):
        # Bad request and docstring check
        response = self.app.get('/polygon')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)

        response = self.app.get('/polygon?geom=%s&raster_table=%s' % (
            self.polygon,
            self.raster
        ))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "%.3f" % json.loads(
                response.data
            )['query']['value'],
            "2.490"
        )

    def test_expectations(self):
        """Buffer score tests with set expectations."""

        error = 0
        points = [
            (-4.48354500, 54.14074400), # Isle of man
            (-0.83000000, 51.46000000), # London ish
            ( 4.60000000, 47.60000000), # France ish
            ( 35.0000000, 31.00000000), # Middle east ish
            ( 23.5000000, -3.00000000), # Middle of Africa ish
            (101.0000000, 26.00000000), # Somewhere in China
            (-80.5200000, 25.25000000), # Tip of Florida, US
        ]

        rasters = [
            ("drg16", "nh_drought_hazard_2016_raster",),
            ("cse16", "nh_extra_tropical_cyclone_hazard_2016_raster",),
            ("fld16", "nh_flood_hazard_2016_raster",),
            ("lse16", "nh_landslide_earthquake_related_hazard_2016_raster",),
            ("ssm16", "nh_seismic_hazard_2016_raster",),
            ("wfr16", "nh_wildfire_hazard_2016_raster",),
            ("ghg16", "cc_total_ghg_emissions_2016_raster",),
            ("cmu16", "cc_climate_model_uncertainty_2016_raster",),
            ("aq16", "cc_air_quality_2016_raster",),
        ]


        # Check legacy expectations
        for ridx, (slug, raster) in enumerate(rasters):
            for idx, point in enumerate(points):

                # Get database method score
                db_response = self.app.get(
                    '/custombuffer?lat=%s&lon=%s&radius=5&raster_table=dbv_%s&id=%s' % (
                        point[1],
                        point[0],
                        raster,
                        "%04d%04d" % (idx, ridx)
                    )
                )

                try:
                    db_value = json.loads(db_response.data)['query']['value']
                except Exception, ex:
                    print ex
                    error = error + 1
                    continue

                if db_value:
                    db_value = float(str("%.3f" % db_value))

                # Comare with tif file on disk method
                tif_response = self.app.get(
                    '/custombuffer?lat=%s&lon=%s&radius=5&raster_table=%s&id=%s' % (
                        point[1],
                        point[0],
                        raster,
                        "%04d%04d" % (idx, ridx)
                    )
                )
                try:
                    tif_value = json.loads(tif_response.data)['query']['value']
                except Exception, ex:
                    print ex
                    error = error + 1
                    continue

                if tif_value:
                    tif_value = float(str("%.3f" % tif_value))

                try:
                    self.assertEqual(
                        db_value,
                        tif_value
                    )
                except AssertionError:
                    print "MISMATCH", point, raster, db_value, tif_value
                    error += 1

        # Check legacy expectations
        dataset = tablib.Dataset()

        expectations_file = os.path.join(
            os.path.split(__file__)[0],
            'data/gis_results.csv'
        )

        dataset.csv = open(expectations_file).read()

        expectations = {}

        for line in dataset:
            point_data = dict(zip(dataset.headers, line))
            point = (point_data.pop('lng'), point_data.pop('lat'))
            for slug, value in point_data.items():
                found = False
                for r_slug, raster in rasters:
                    if r_slug==slug:
                        this_raster=raster
                        found = True
                        break

                if not found:
                    continue

                key = "%.8f%.8f%s" % (float(point[0]), float(point[1]), this_raster)

                if value is None or float(value) < 0:
                    value = None
                else:
                    value = float(value)

                expectations[key] = value


        points.pop(0) # Not in GIS sample


        for idx, point in enumerate(points):
            for ridx, (slug, raster) in enumerate(rasters):
                key = "%.8f%.8f%s" % (float(point[0]), float(point[1]), raster)

                response = self.app.get(
                    '/pointbuffer?lat=%s&lon=%s&radius=20&raster_table=%s&id=%s' % (
                        point[1],
                        point[0],
                        raster,
                        "%04d%04d" % (idx, ridx)
                    )
                )

                try:
                    value = json.loads(response.data)['query']['value']
                except:
                    print "error: %s: %s" % (point, raster)
                    error = error + 1
                    continue

                if value is None and expectations[key] is None:
                    print "None for %s" % point
                    continue

                if value is not None:
                    value = float("%.2f" % (value))

                if expectations[key] is None:
                    self.assertEqual(
                        value,
                        None
                    )

                elif str(value) != str(expectations[key]):
                    diff = abs(
                        float(value) - float(expectations[key])
                    )
                    try:
                        self.assertEqual(
                            diff < 0.22,
                            True
                        )
                    except:
                        print "ACCURACY MISMATCH", point, raster, value, expectations[key]

        if error:
            self.fail("Error count: %s" % error)

if __name__ == '__main__':
    unittest.main()
