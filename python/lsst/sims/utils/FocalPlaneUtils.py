import numpy as np
import palpy
from lsst.sims.utils.CodeUtilities import _validate_inputs
from lsst.sims.utils import _observedFromICRS, _icrsFromObserved

__all__ = ["_pupilCoordsFromRaDec", "pupilCoordsFromRaDec",
           "_raDecFromPupilCoords", "raDecFromPupilCoords"]


def pupilCoordsFromRaDec(ra_in, dec_in, obs_metadata=None, epoch=2000.0):
    """
    Take an input RA and dec from the sky and convert it to coordinates
    on the focal plane.

    This uses PAL's gnomonic projection routine which assumes that the focal
    plane is perfectly flat.  The output is in Cartesian coordinates, assuming
    that the Celestial Sphere is a unit sphere.

    The RA, Dec accepted by this method are in the International Celestial
    Reference System.  Before applying the gnomonic projection, this method
    transforms those RA, Dec into observed geocentric coordinates, applying
    the effects of precession, nutation, aberration, parallax and refraction.
    This is done, because the gnomonic projection ought to be applied to what
    observers actually see, rather than the idealized, above-the-atmosphere
    coordinates represented by the ICRS.

    @param [in] ra_in is in degrees (ICRS).  Can be either a numpy array or a float.

    @param [in] dec_in is in degrees (ICRS).  Can be either a numpy array or a float.

    @param [in] obs_metadata is an ObservationMetaData instantiation characterizing the
    telescope location and pointing.

    @param [in] epoch is the epoch of mean ra and dec in julian years (default=2000.0)

    @param [out] returns a numpy array whose first row is the x coordinate on the pupil in
    radians and whose second row is the y coordinate in radians
    """

    return _pupilCoordsFromRaDec(np.radians(ra_in), np.radians(dec_in),
                                 obs_metadata=obs_metadata, epoch=epoch)


def _pupilCoordsFromRaDec(ra_in, dec_in, obs_metadata=None, epoch=2000.0):
    """
    Take an input RA and dec from the sky and convert it to coordinates
    on the focal plane.

    This uses PAL's gnomonic projection routine which assumes that the focal
    plane is perfectly flat.  The output is in Cartesian coordinates, assuming
    that the Celestial Sphere is a unit sphere.

    The RA, Dec accepted by this method are in the International Celestial
    Reference System.  Before applying the gnomonic projection, this method
    transforms those RA, Dec into observed geocentric coordinates, applying
    the effects of precession, nutation, aberration, parallax and refraction.
    This is done, because the gnomonic projection ought to be applied to what
    observers actually see, rather than the idealized, above-the-atmosphere
    coordinates represented by the ICRS.

    @param [in] ra_in is in radians (ICRS).  Can be either a numpy array or a float.

    @param [in] dec_in is in radians (ICRS).  Can be either a numpy array or a float.

    @param [in] obs_metadata is an ObservationMetaData instantiation characterizing the
    telescope location and pointing.

    @param [in] epoch is the epoch of mean ra and dec in julian years (default=2000.0)

    @param [out] returns a numpy array whose first row is the x coordinate on the pupil in
    radians and whose second row is the y coordinate in radians
    """

    are_arrays = _validate_inputs([ra_in, dec_in], ['ra_in', 'dec_in'],
                                  "pupilCoordsFromRaDec")

    if obs_metadata is None:
        raise RuntimeError("Cannot call pupilCoordsFromRaDec without obs_metadata")

    if obs_metadata.mjd is None:
        raise RuntimeError("Cannot call pupilCoordsFromRaDec; obs_metadata.mjd is None")

    if epoch is None:
        raise RuntimeError("Cannot call pupilCoordsFromRaDec; epoch is None")

    if obs_metadata.rotSkyPos is None:
        #there is no observation meta data on which to base astrometry
        raise RuntimeError("Cannot calculate [x,y]_focal_nominal without obs_metadata.rotSkyPos")

    if obs_metadata.pointingRA is None or obs_metadata.pointingDec is None:
        raise RuntimeError("Cannot calculate [x,y]_focal_nominal without pointingRA and Dec in obs_metadata")

    theta = obs_metadata._rotSkyPos

    ra_obs, dec_obs = _observedFromICRS(ra_in, dec_in, obs_metadata=obs_metadata,
                                        epoch=epoch, includeRefraction=True)

    ra_pointing, dec_pointing = _observedFromICRS(obs_metadata._pointingRA,
                                                  obs_metadata._pointingDec,
                                                  obs_metadata=obs_metadata,
                                                  epoch=epoch, includeRefraction=True)

    #palpy.ds2tp performs the gnomonic projection on ra_in and dec_in
    #with a tangent point at (pointingRA, pointingDec)
    #
    if not are_arrays:
        try:
            x, y = palpy.ds2tp(ra_obs, dec_obs, ra_pointing, dec_pointing)
        except:
            x = np.NaN
            y = np.NaN
    else:
        try:
            x, y = palpy.ds2tpVector(ra_obs, dec_obs, ra_pointing, dec_pointing)
        except:
            # apparently, one of your ra/dec values was improper; we will have to do this
            # element-wise, putting NaN in the place of the bad values
            x = []
            y = []
            for rr, dd in zip(ra_obs, dec_obs):
                try:
                    xx, yy = palpy.ds2tp(rr, dd, ra_pointing, dec_pointing)
                except:
                    xx = np.NaN
                    yy = np.NaN
                x.append(xx)
                y.append(yy)
            x = np.array(x)
            y = np.array(y)


    # The extra negative sign on x_out comes from the following:
    # The Gnomonic projection as calculated by palpy is such that,
    # if north is in the +y direction, then west is in the -x direction,
    # which is the opposite of the behavior we want (I do not know how to
    # express this analytically; I have just confirmed it numerically)
    x *= -1.0

    # rotate the result by rotskypos (rotskypos being "the angle of the sky relative to
    # camera coordinates" according to phoSim documentation) to account for
    # the rotation of the focal plane about the telescope pointing

    x_out = x*np.cos(theta) - y*np.sin(theta)
    y_out = x*np.sin(theta) + y*np.cos(theta)

    return np.array([x_out, y_out])


def raDecFromPupilCoords(xPupil, yPupil, obs_metadata=None, epoch=2000.0):
    """
    @param [in] xPupil -- pupil coordinates in radians.
    Can be a numpy array or a float.

    @param [in] yPupil -- pupil coordinates in radians.
    Can be a numpy array or a float.

    @param [in] obs_metadata -- an instantiation of ObservationMetaData characterizing
    the state of the telescope

    @param [in] epoch -- julian epoch of the mean equinox used for the coordinate
    transformations (in years; defaults to 2000)

    @param [out] a 2-D numpy array in which the first row is RA and the second
    row is Dec (both in degrees; both in the International Celestial Reference System)
    """

    output = _raDecFromPupilCoords(xPupil, yPupil, obs_metadata=obs_metadata,
                                               epoch=epoch)

    return np.degrees(output)


def _raDecFromPupilCoords(xPupil, yPupil, obs_metadata=None, epoch=2000.0):
    """
    @param [in] xPupil -- pupil coordinates in radians.
    Can be a numpy array or a float.

    @param [in] yPupil -- pupil coordinates in radians.
    Can be a numpy array or a float.

    @param [in] obs_metadata -- an instantiation of ObservationMetaData characterizing
    the state of the telescope

    @param [in] epoch -- julian epoch of the mean equinox used for the coordinate
    transformations (in years; defaults to 2000)

    @param [out] a 2-D numpy array in which the first row is RA and the second
    row is Dec (both in radians; both in the International Celestial Reference System)
    """

    are_arrays = _validate_inputs([xPupil, yPupil], ['xPupil', 'yPupil'],
                                 "raDecFromPupilCoords")

    if obs_metadata is None:
        raise RuntimeError("Cannot call raDecFromPupilCoords without obs_metadata")

    if epoch is None:
        raise RuntimeError("Cannot call raDecFromPupilCoords; epoch is None")

    if obs_metadata.rotSkyPos is None:
        raise RuntimeError("Cannot call raDecFromPupilCoords without rotSkyPos " + \
                           "in obs_metadata")

    if obs_metadata.pointingRA is None or obs_metadata.pointingDec is None:
        raise RuntimeError("Cannot call raDecFromPupilCoords "+ \
                          "without pointingRA, pointingDec in obs_metadata")

    if obs_metadata.mjd is None:
        raise RuntimeError("Cannot calculate x_pupil, y_pupil without mjd " + \
                           "in obs_metadata")

    ra_pointing, dec_pointing = _observedFromICRS(obs_metadata._pointingRA,
                                                  obs_metadata._pointingDec,
                                                  obs_metadata=obs_metadata,
                                                  epoch=epoch, includeRefraction=True)

    #This is the same as theta in pupilCoordsFromRaDec, except without the minus sign.
    #This is because we will be reversing the rotation performed in that other method.
    theta = -1.0*obs_metadata._rotSkyPos

    x_g = xPupil*np.cos(theta) - yPupil*np.sin(theta)
    y_g = xPupil*np.sin(theta) + yPupil*np.cos(theta)

    x_g *= -1.0

    # x_g and y_g are now the x and y coordinates
    # can now use the PALPY method palDtp2s to convert to RA, Dec.

    if are_arrays:
        raObs, decObs = palpy.dtp2sVector(x_g, y_g, ra_pointing, dec_pointing)
    else:
        raObs, decObs = palpy.dtp2s(x_g, y_g, ra_pointing, dec_pointing)

    ra_icrs, dec_icrs = _icrsFromObserved(raObs, decObs,
                                          obs_metadata=obs_metadata,
                                          epoch=epoch, includeRefraction=True)

    return np.array([ra_icrs, dec_icrs])
