import os
import json
import app
import unittest
import tempfile

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


    def test_value_at_point(self):
        # Bad request and docstring check
        response = self.app.get('/point')
        self.assertEqual(response.status_code, 400)
        self.assertEqual('Expects:' in response.data, True)


    def test_legacy_buffer_value_at_point(self):

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
            json.loads(
                response.data
            )['query']['value'],
            2.490
        )

if __name__ == '__main__':
    unittest.main()
