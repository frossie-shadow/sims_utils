from __future__ import with_statement
import numpy as np
import warnings
import unittest
import lsst.utils.tests as utilsTests
import lsst.sims.utils as utils


class TimeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Create list of control TAI and UTC values.

        UTC values are generated by entering calendar dates into the USNO
        JD calculator at

        http://aa.usno.navy.mil/data/docs/JulianDate.php

        TAI values are found from this table listing the relationship between
        TAI and UTC as a function of epoch

        https://hpiers.obspm.fr/eop-pc/earthor/utc/TAI-UTC_tab.html
        """

        jd_to_mjd = 2400000.5
        sec_to_day = 1.0/86400.0

        cls.utc_control = []
        cls.tai_control = []
        cls.year = []

        # all UTC values calculated at midnight UT
        # June 10, 1961
        mjd = 2437460.5 - jd_to_mjd
        dt = 1.4228180 + (mjd-37300.0)*0.001296
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1961)

        # June 10, 1962
        mjd = 2437825.5 - jd_to_mjd
        dt = 1.8458580 + (mjd-37665.0)*0.0011232
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1962)

        # June 10, 1963
        mjd = 2438190.5 - jd_to_mjd
        dt = 1.8458580 + (mjd - 37665.0) * 0.0011232
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1963)

        # June 10, 1964
        mjd = 2438556.5 - jd_to_mjd
        dt = 3.3401300 + (mjd - 38761.0)*0.001296
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1964)

        # June 10, 1965
        mjd = 2438921.5 - jd_to_mjd
        dt = 3.6401300 + (mjd-38761.0)*0.001296
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1965)

        # June 10, 1974
        mjd = 2442208.5 - jd_to_mjd
        dt = 13.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1974)

        # June 10, 1984
        mjd = 2445861.5 - jd_to_mjd
        dt = 22.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1984)

        # June 10, 1994
        mjd = 2449513.5 - jd_to_mjd
        dt = 28.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1994)

        # June 10, 1997
        mjd = 2450609.5 - jd_to_mjd
        dt = 30.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(1997)

        # June 10, 2003
        mjd = 2452800.5 - jd_to_mjd
        dt = 32.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(2003)

        # June 10, 2013
        mjd = 2456453.5 - jd_to_mjd
        dt = 35.0
        cls.utc_control.append(mjd)
        cls.tai_control.append(mjd + dt*sec_to_day)
        cls.year.append(2013)


    def test_tai_from_utc(self):
        """
        Test our transformation from UTC to TAI.
        """
        for utc, tai, year in \
            zip(self.utc_control, self.tai_control, self.year):

            tai_test = utils.taiFromUtc(utc)
            msg = "year: %s... %.12f != %.12f" % (year, tai, tai_test)
            self.assertAlmostEqual(tai_test, tai, 12, msg=msg)


    def test_utc_from_tai(self):
        """
        Test our transformation from TAI to UTC
        """
        for utc, tai, year in \
            zip(self.utc_control, self.tai_control, self.year):

            utc_test = utils.utcFromTai(tai)
            msg = "year: %s... %.12f != %.12f" % (year, utc, utc_test)
            self.assertAlmostEqual(utc_test, utc, 23, msg=msg)


    def test_boundary_values(self):
        """
        Because utcFromTai relies on interpolating results of
        taiFromUtc, we will test the round-trip on some boundary values.

        Data taken from

        https://hpiers.obspm.fr/eop-pc/earthor/utc/TAI-UTC_tab.html

        and

        http://aa.usno.navy.mil/data/docs/JulianDate.php
        """

        jd_to_mjd = 2400000.5
        boundary_values = []
        boundary_values.append(2439004.5 - jd_to_mjd) # September 1, 1965
        boundary_values.append(2443144.5 - jd_to_mjd) # January 1, 1977
        boundary_values.append(2450083.5 - jd_to_mjd) # January 1, 1996
        boundary_values.append(2439126.5 - jd_to_mjd) # January 1, 1966
        boundary_values.append(2456109.5 - jd_to_mjd) # July 1, 2012

        for bv in boundary_values:
            for utc in np.arange(bv-1.0e-5, bv+1.0e-5, 1.0e-6):
                tai = utils.taiFromUtc(utc)
                utc_test = utils.utcFromTai(tai)
                self.assertAlmostEqual(utc_test, utc, 15)


    def test_dut_from_utc(self):
        """
        Test our calculation of UT1-UTC from utc by just checking
        that the values from our lookup table are properly applied.
        """

        utc_control = [48622.0, 48638.0, 49528.0, 51638.0,
                       53933.0]

        dt_control = [-0.12516880, -0.16103330, -0.20954640, 0.27327980,
                      0.18471120]

        for utc, dt in zip(utc_control, dt_control):
            dt_test = utils.dutFromUtc(utc)
            self.assertAlmostEqual(dt, dt_test, 7)


    def test_dut_warnings(self):
        """
        Test that a warning is raised if you ask dutFromUTC to calculate
        UT1-UTC for a UTC value that is outside the span of our data.
        """

        # Note: the values fed to dutFromUtc in this unit test must be
        # distinct from the values passed into test_ut1_warnings,
        # otherwise, warnings will suppress the warning as already
        # having been raised

        with warnings.catch_warnings(record=True) as context:
            ut1 = utils.dutFromUtc(48619.5)
        self.assertEqual(ut1, 0.0)
        self.assertIn("We will return UT1-UTC = 0, for lack of a better idea",
                      str(context[-1].message))

        with warnings.catch_warnings(record=True) as context:
            ut1 = utils.dutFromUtc(57712.5)
        self.assertEqual(ut1, 0.0)
        self.assertIn("We will return UT1-UTC = 0, for lack of a better idea",
                      str(context[-1].message))


    def test_ut1_from_utc(self):
        """
        Test our conversion from UT1 to UTC by just checking that the
        values from our lookup table are properly applied.
        """

        utc_control = [48622.0, 48638.0, 49528.0, 51638.0,
                       53933.0]

        dt_control = [-0.12516880, -0.16103330, -0.20954640, 0.27327980,
                      0.18471120]

        sec_to_day = 1.0/86400.0
        for utc, dt in zip(utc_control, dt_control):
            ut1 = utils.ut1FromUtc(utc)
            dd = (ut1-utc)/sec_to_day
            self.assertAlmostEqual(dd, dt, 6)
            # adding dt to the utc introduces some rounding error,
            # so we do not get back the full 7 decimal places
            # specified by the data


    def test_utc_from_ut1(self):
        """
        Test that utcFromUt1 really does invert ut1FromUtc
        """

        np.random.seed(45)

        utc_arr = 48622.0 + (57711.0-48622.0)*np.random.random_sample(1000)
        ut1_arr = np.array([utils.ut1FromUtc(utc) for utc in utc_arr])
        utc_test = np.array([utils.utcFromUt1(ut1) for ut1 in ut1_arr])
        np.testing.assert_array_almost_equal(utc_arr, utc_test, 6)


    def test_ut1_warnings(self):
        """
        Test that a warning is raised if you ask ut1FromUtc to calculate
        UT1 for a UTC value that is outside the span of our data.
        """

        # Note: the values fed to ut1FromUtc in this unit test must be
        # distinct from the values passed into test_dut_warnings,
        # otherwise, warnings will suppress the warning as already
        # having been raised

        with warnings.catch_warnings(record=True) as context:
            ut1 = utils.ut1FromUtc(48621.5)
        self.assertEqual(ut1, 48621.5)
        self.assertIn("We will return UT1-UTC = 0, for lack of a better idea",
                      str(context[-1].message))

        with warnings.catch_warnings(record=True) as context:
            ut1 = utils.ut1FromUtc(57711.5)
        self.assertEqual(ut1, 57711.5)
        self.assertIn("We will return UT1-UTC = 0, for lack of a better idea",
                      str(context[-1].message))


    def test_dtt_from_utc(self):
        """
        Test our method to find TT-TAI in seconds
        """

        precision = 11 # expect 0.1 nanonsecond precision

        self.assertAlmostEqual(utils.dttFromUtc(42588.0), 32.1840, precision)

        self.assertAlmostEqual(utils.dttFromUtc(57020.0), 32.1840276970, precision)

        self.assertAlmostEqual(utils.dttFromUtc(43679.0), 32.1840054460, precision)

        self.assertAlmostEqual(utils.dttFromUtc(46459.0), 32.1840146120, precision)

        self.assertAlmostEqual(utils.dttFromUtc(52629.0), 32.1840262340, precision)

        self.assertAlmostEqual(utils.dttFromUtc(56829.0), 32.1840276936, precision)

        self.assertAlmostEqual(utils.dttFromUtc(56999.0), 32.1840276961, precision)


    def test_tt_from_tai(self):
        """
        Test our method to convert from TAI to TT (Terrestrial Time)
        """

        np.random.seed(99)
        tai_arr = np.random.random_sample(10)+43000.0

        for tai in tai_arr:
            self.assertAlmostEqual(utils.ttFromTai(tai), tai+0.00037250, 8)


    def test_tdb_from_tt(self):
        """
        Test our method to convert from Terrestrial Time (TT) to Barycentric Dynamical Time (TDB)
        """

        sec_to_day = 1.0/86400.0

        tt_control = [57388.645, 46132.112]
        jd_minus_control = [5844.15, -5412.39] # the rounding of the JD to two decimals
                                             # and subtracting of 2451545.0 was done by
                                             # hand, to check that tdbFromTt does it correctly

        for tt, jd in zip(tt_control, jd_minus_control):
            gg_deg = 357.53 + 0.9856003*jd
            gg_rad = np.radians(gg_deg)
            dt = 0.001658*np.sin(gg_rad) + 0.000014*np.sin(2.0*gg_rad)
            tdb = utils.tdbFromTt(tt)
            dt_test = (tdb-tt)/sec_to_day
            self.assertAlmostEqual(dt_test, dt, 6)


    def test_modified_julian_date_class(self):
        """
        Test the construction of ModifiedJulianDate
        """
        mjd1 = utils.ModifiedJulianDate(TAI=57388.0)
        mjd2 = utils.ModifiedJulianDate(UTC=mjd1.UTC)
        self.assertEqual(mjd1.TAI, mjd2.TAI)
        self.assertEqual(mjd1.UTC, mjd2.UTC)
        self.assertEqual(mjd1.TT, mjd2.TT)
        self.assertEqual(mjd1.TDB, mjd2.TDB)
        self.assertEqual(mjd1.dut, mjd2.dut)

        with self.assertRaises(RuntimeError) as context:
            mjd3 = utils.ModifiedJulianDate()
        self.assertEqual(context.exception.args[0],
                         "You must specify either TAI or UTC to "
                         "instantiate ModifiedJulianDate")


def suite():
    """Returns a suite containing all the test cases in this module."""
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(TimeTest)

    return unittest.TestSuite(suites)

def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)