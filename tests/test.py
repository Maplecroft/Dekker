import os
import json
import app
import unittest
import tempfile
import tablib

class DekkerTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
        app.app.config['TESTING'] = True
        self.app = app.app.test_client()

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
        os.unlink(app.app.config['DATABASE'])


    def notest_value_at_point(self):
        # Bad request and docstring check
        response = self.app.get('/point')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)


    def notest_legacy_buffer_value_at_point(self):

        # Bad request and docstring check
        response = self.app.get('/buffer')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)

        # Expected 3.872 for nh_extra_tropical_cyclone_hazard_2016_raster
        # for legacy calculation method
        response = self.app.get(
            '/buffer?lat=%s&lon=%s&radius=25&raster_table=%s' % (
                self.point[1],
                self.point[0],
                self.raster
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(
                response.data
            )['query']['value'],
            3.872
        )

        # Test no difference on radius change
        response = self.app.get(
            '/buffer?lat=%s&lon=%s&radius=35&raster_table=%s' % (
                self.point[1],
                self.point[0],
                self.raster
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(
                response.data
            )['query']['value'],
            3.872
        )

    def notest_buffer_value_at_point(self):

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
            json.loads(
                response.data
            )['query']['value'],
            2.680
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
            json.loads(
                response.data
            )['query']['value'],
            3.12
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
            json.loads(
                response.data
            )['query']['value'],
            3.12
        )

    def notest_polygon(self):
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
            json.loads(
                response.data
            )['query']['value'],
            2.490
        )

    def test_expectations(self):
        """Buffer score tests with set expectations."""
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
            ("ppx16", "nh_natural_hazards_population_exposure_abs_2016_raster",),
            ("ssm16", "nh_seismic_hazard_2016_raster",),
            ("wfr16", "nh_wildfire_hazard_2016_raster",),
            ("ghg16", "cc_total_ghg_emissions_2016_raster",),
            ("cmu16", "cc_climate_model_uncertainty_2016_raster",),
            ("aq16", "cc_air_quality_2016_raster",),
        ]

        legacy_expecations = json.loads(
            open(
                os.path.join(
                    os.path.split(__file__)[0],
                    'data/legacy_scores.json'
                )
            ).read()
        )

        # Check legacy expectations
        for idx, point in enumerate(points):
            break
            for ridx, (slug, raster) in enumerate(rasters):
                key = "%.2f%.2f%s" % (point[0], point[1], raster)

                #from api.proxy.views import dekker_raster_score
                #legacy_expecations[key] = dekker_raster_score(
                #    point[1], point[0], raster, 999, 25, no_value=None,
                #    query_type='buffer'
                #)

                response = self.app.get(
                    '/buffer?lat=%s&lon=%s&radius=5&raster_table=%s&id=%s' % (
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
                    self.fail()

                self.assertEqual(
                    legacy_expecations[key],
                    value,
                )

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
                    self.fail()

                if value is None and expectations[key] is None:
                    print "None for %s" % point
                    continue

                if value is not None:
                    value = float("%.2f" % (value))

                if str(value) != str(expectations[key]):
                    if value is not None:
                        diff = abs(
                            float(value) - float(expectations[key])
                        )
                        self.assertEqual(
                            diff < 0.22,
                            True
                        )
                    else:
                        self.assertEqual(
                            str(value),
                            str(expectations[key])
                        )

if __name__ == '__main__':
    unittest.main()
