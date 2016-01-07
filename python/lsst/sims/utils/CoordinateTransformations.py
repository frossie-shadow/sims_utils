import numpy
import palpy
from collections import OrderedDict

__all__ = ["_galacticFromEquatorial", "galacticFromEquatorial",
           "_equatorialFromGalactic", "equatorialFromGalactic",
           "sphericalFromCartesian", "cartesianFromSpherical",
           "rotationMatrixFromVectors",
           "equationOfEquinoxes", "calcGmstGast", "calcLmstLast",
           "haversine",
           "calcObsDefaults", "makeObservationMetadata", "makeObsParamsAzAltTel",
           "makeObsParamsAzAltSky", "makeObsParamsRaDecTel", "makeObsParamsRaDecSky",
           "arcsecFromRadians", "radiansFromArcsec",
           "arcsecFromDegrees", "degreesFromArcsec"]


def calcLmstLast(mjd, longRad):
    """
    calculates local mean sidereal time and local apparent sidereal time

    @param [in] mjd is the universal time expressed as an MJD.
    This can be a numpy array or a single value.

    @param [in] longRad is the longitude in radians (positive east of the prime meridian)
    This can be numpy array or a single value.  If a numpy array, should have the same length as mjd.  In that
    case, each longRad will be applied only to the corresponding mjd.

    @param [out] lmst is the local mean sidereal time in hours

    @param [out] last is the local apparent sideral time in hours
    """
    mjdIsArray = False
    longRadIsArray = False
    if isinstance(mjd, numpy.ndarray):
        mjdIsArray = True

    if isinstance(longRad, numpy.ndarray):
        longRadIsArray = True

    if longRadIsArray and mjdIsArray:
        if len(longRad) != len(mjd):
            raise RuntimeError("in calcLmstLast mjd and longRad have different lengths")

    if longRadIsArray and not mjdIsArray:
        raise RuntimeError("in calcLmstLast longRad is numpy array but mjd is not")

    longDeg0 = numpy.degrees(longRad)
    longDeg0 %= 360.0

    if longRadIsArray:
        longDeg = numpy.where(longDeg0>180.0, longDeg0-360.0, longDeg0)
    else:
        if longDeg0 > 180.:
            longDeg = longDeg0-360.
        else:
            longDeg = longDeg0

    hrs = longDeg/15.
    gmstgast = calcGmstGast(mjd)
    lmst = gmstgast[0]+hrs
    last = gmstgast[1]+hrs
    lmst %= 24.
    last %= 24.
    return lmst, last


def galacticFromEquatorial(ra, dec):
    '''Convert RA,Dec (J2000) to Galactic Coordinates

    @param [in] ra is right ascension in degrees, either a float or a numpy array

    @param [in] dec is declination in degrees, either a float or a numpy array

    @param [out] gLong is galactic longitude in degrees

    @param [out] gLat is galactic latitude in degrees
    '''

    gLong, gLat = _galacticFromEquatorial(numpy.radians(ra), numpy.radians(dec))
    return numpy.degrees(gLong), numpy.degrees(gLat)


def _galacticFromEquatorial(ra, dec):
    '''Convert RA,Dec (J2000) to Galactic Coordinates

    All angles are in radians

    @param [in] ra is right ascension in radians, either a float or a numpy array

    @param [in] dec is declination in radians, either a float or a numpy array

    @param [out] gLong is galactic longitude in radians

    @param [out] gLat is galactic latitude in radians
    '''

    if isinstance(ra, numpy.ndarray):
        gLong, gLat = palpy.eqgalVector(ra, dec)
    else:
        gLong, gLat = palpy.eqgal(ra, dec)

    return gLong, gLat


def equatorialFromGalactic(gLong, gLat):
    '''Convert Galactic Coordinates to RA, dec (J2000)

    @param [in] gLong is galactic longitude in degrees, either a float or a numpy array
    (0 <= gLong <= 360.)

    @param [in] gLat is galactic latitude in degrees, either a float or a numpy array
    (-90. <= gLat <= 90.)

    @param [out] ra is right ascension in degrees

    @param [out] dec is declination in degrees
    '''

    ra, dec = _equatorialFromGalactic(numpy.radians(gLong), numpy.radians(gLat))
    return numpy.degrees(ra), numpy.degrees(dec)


def _equatorialFromGalactic(gLong, gLat):
    '''Convert Galactic Coordinates to RA, dec (J2000)

    @param [in] gLong is galactic longitude in radians, either a float or a numpy array
    (0 <= gLong <= 2*pi)

    @param [in] gLat is galactic latitude in radians, either a float or a numpy array
    (-pi/2 <= gLat <= pi/2)

    @param [out] ra is right ascension in radians (J2000)

    @param [out] dec is declination in radians (J2000)
    '''

    if isinstance(gLong, numpy.ndarray):
        ra, dec = palpy.galeqVector(gLong, gLat)
    else:
        ra, dec = palpy.galeq(gLong, gLat)

    return ra, dec


def cartesianFromSpherical(longitude, latitude):
    """
    Transforms between spherical and Cartesian coordinates.

    @param [in] longitude is a numpy array of longitudes

    @param [in] latitude is a numpy array of latitudes

    @param [out] a numpy array of the (three-dimensional) cartesian coordinates on a unit sphere

    All angles are in radians
    """

    if not isinstance(longitude, numpy.ndarray) or not isinstance(latitude, numpy.ndarray):
        raise RuntimeError("you need to pass numpy arrays to cartesianFromSpherical")

    cosDec = numpy.cos(latitude)
    return numpy.array([numpy.cos(longitude)*cosDec,
                      numpy.sin(longitude)*cosDec,
                      numpy.sin(latitude)]).transpose()


def sphericalFromCartesian(xyz):
    """
    Transforms between Cartesian and spherical coordinates

    @param [in] xyz is a numpy array of points in 3-D space.
    Each row is a different point.

    @param [out] returns longitude and latitude

    All angles are in radians
    """

    if not isinstance(xyz, numpy.ndarray):
        raise RuntimeError("you need to pass a numpy array to sphericalFromCartesian")

    if len(xyz.shape)>1:
        rad = numpy.sqrt(numpy.power(xyz,2).sum(axis=1))
        longitude = numpy.arctan2( xyz[:,1], xyz[:,0])
        latitude = numpy.arcsin( xyz[:,2] / rad)
    else:
        rad = numpy.sqrt(numpy.dot(xyz,xyz))
        longitude = numpy.arctan2(xyz[1], xyz[0])
        latitude = numpy.arcsin(xyz[2]/rad)

    return longitude, latitude


def rotationMatrixFromVectors(v1, v2):
    '''
    Given two vectors v1,v2 calculate the rotation matrix for v1->v2 using the axis-angle approach

    @param [in] v1, v2 are two Cartesian unit vectors (in three dimensions)

    @param [out] rot is the rotation matrix that rotates from one to the other

    '''

    if numpy.abs(numpy.sqrt(numpy.dot(v1,v1))-1.0) > 0.01:
        raise RuntimeError("v1 in rotationMatrixFromVectors is not a unit vector")

    if numpy.abs(numpy.sqrt(numpy.dot(v2,v2))-1.0) > 0.01:
        raise RuntimeError("v2 in rotationMatrixFromVectors is not a unit vector")

    # Calculate the axis of rotation by the cross product of v1 and v2
    cross = numpy.cross(v1,v2)
    cross = cross / numpy.sqrt(numpy.dot(cross,cross))

    # calculate the angle of rotation via dot product
    angle  = numpy.arccos(numpy.dot(v1,v2))
    sinDot = numpy.sin(angle)
    cosDot = numpy.cos(angle)

    # calculate the corresponding rotation matrix
    # http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle
    rot = [[cosDot + cross[0]*cross[0]*(1-cosDot), -cross[2]*sinDot+(1-cosDot)*cross[0]*cross[1], \
            cross[1]*sinDot + (1-cosDot)*cross[0]*cross[2]],\
            [cross[2]*sinDot+(1-cosDot)*cross[0]*cross[1], cosDot + (1-cosDot)*cross[1]*cross[1], \
            -cross[0]*sinDot+(1-cosDot)*cross[1]*cross[2]], \
            [-cross[1]*sinDot+(1-cosDot)*cross[0]*cross[2], \
            cross[0]*sinDot+(1-cosDot)*cross[1]*cross[2], \
            cosDot + (1-cosDot)*(cross[2]*cross[2])]]

    return rot


def equationOfEquinoxes(d):
    """
    The equation of equinoxes. See http://aa.usno.navy.mil/faq/docs/GAST.php

    @param [in] d is either a numpy array or a float that is Terrestrial Time
    expressed as an MJD

    @param [out] the equation of equinoxes in radians.
    """

    if isinstance(d, numpy.ndarray):
        return palpy.eqeqxVector(d)
    else:
        return palpy.eqeqx(d)


def calcGmstGast(mjd):
    """
    Compute Greenwich mean sidereal time and Greenwich apparent sidereal time
    see: From http://aa.usno.navy.mil/faq/docs/GAST.php

    @param [in] mjd is the universal time expressed as an MJD

    @param [out] gmst Greenwich mean sidereal time in hours

    @param [out] gast Greenwich apparent sidereal time in hours
    """

    date = numpy.floor(mjd)
    ut1 = mjd-date
    if isinstance(mjd, numpy.ndarray):
        gmst = palpy.gmstaVector(date, ut1)
    else:
        gmst = palpy.gmsta(date, ut1)

    eqeq = equationOfEquinoxes(mjd)
    gast = gmst + eqeq

    gmst = gmst*24.0/(2.0*numpy.pi)
    gmst %= 24.0

    gast = gast*24.0/(2.0*numpy.pi)
    gast %= 24.0

    return gmst, gast


def haversine(long1, lat1, long2, lat2):
    """
    Return the angular distance between two points in radians

    @param [in] long1 is the longitude of point 1 in radians

    @param [in] lat1 is the latitude of point 1 in radians

    @param [in] long2 is the longitude of point 2 in radians

    @param [in] lat2 is the latitude of point 2 in radians

    @param [out] the angular separation between points 1 and 2 in radians

    From http://en.wikipedia.org/wiki/Haversine_formula
    """
    t1 = numpy.sin(lat2/2.-lat1/2.)**2
    t2 = numpy.cos(lat1)*numpy.cos(lat2)*numpy.sin(long2/2. - long1/2.)**2
    return 2*numpy.arcsin(numpy.sqrt(t1 + t2))


def calcObsDefaults(raRad, decRad, altRad, azRad, rotTelRad, mjd, band, longRad, latRad):
    """
    Fromats input data into a dict of metadata that PhoSim expect.

    Users should probably not be calling this by hand, as it makes no effort to ensure that
    the input values are self-consistent.  This method is called by
    makeObsParamsAzAltTel
    makeObsParamsAzAltSky
    makeObsPeramsRaDecTel
    makeObsParamsRaDecSky
    which do ensure self-consistency of values.

    @param [in] raRad is RA in radians

    @param [in] decRad is Dec in radians

    @param [in] altRad is altitude in radians

    @param [in] azRad is azimuth in radians

    @param [in] rotTelRad is rotTelPos in radians

    @param [in] mjd is the Universal Time expressed as an MJD

    @param [in] band is 'u', 'g', 'r', 'i', 'z', or 'y'
    (i.e. the bandpass of the observation)

    @param [in] longRad is the observer's longitude in radians
    (positive east of the prime meridan)

    @param [in] latRad is the observer's latitude in radians
    (positive north of the equator)

    @param [out] a dict of meta data which PhoSim expects in the
    headers of its input InstanceCatalogs
    """
    obsMd = {}
    #Defaults
    moonra, moondec = _raDecFromAltAz(-numpy.pi/2., 0., longRad, latRad, mjd)
    sunalt = -numpy.pi/2.
    moonalt = -numpy.pi/2.
    dist2moon = haversine(moonra, moondec, raRad, decRad)
    obsMd['Opsim_moonra'] = moonra
    obsMd['Opsim_moondec'] = moondec
    obsMd['Opsim_sunalt'] = sunalt
    obsMd['Opsim_moonalt'] = moonalt
    obsMd['Opsim_dist2moon'] = dist2moon

    rotSkyPos = _getRotSkyPos(raRad, decRad, longRad, latRad, mjd, rotTelRad)
    obsMd['Opsim_filter'] = band
    obsMd['pointingRA'] = raRad
    obsMd['pointingDec'] = decRad
    obsMd['Opsim_rotskypos'] = rotSkyPos
    obsMd['Opsim_rottelpos'] = rotTelRad
    obsMd['Unrefracted_Altitude'] = altRad
    obsMd['Unrefracted_Azimuth'] = azRad
    return obsMd


def makeObservationMetadata(metaData):
    return OrderedDict([(k,(metaData[k], numpy.asarray(metaData[k]).dtype))
                         for k in metaData])


def makeObsParamsAzAltTel(azRad, altRad, mjd, band, rotTelRad=0., longRad=-1.2320792, latRad=-0.517781017, **kwargs):
    '''
    Calculate a minimal set of observing parameters give the ra, dec, and time of the observation.
    altRad -- Altitude of the boresite of the observation in radians
    azRad -- Azimuth of the boresite of the observation in radians
    mjd -- MJD of the observation
    band -- bandpass of the observation e.g. 'r'
    rotTelRad -- Rotation of the camera relative to the telescope in radians Default=0.
    longRad -- Longitude of the observatory in radians Default=-1.2320792
    latRad -- Latitude of the observatory in radians Default=-0.517781017
    **kwargs -- The kwargs will be put in the returned dictionary overriding the default value if it exists
    '''

    raRad, decRad = _raDecFromAltAz(altRad, azRad, longRad, latRad, mjd)
    obsMd = calcObsDefaults(raRad, decRad, altRad, azRad, rotTelRad, mjd, band, longRad, latRad)
    obsMd.update(kwargs)
    return makeObservationMetadata(obsMd)


def makeObsParamsAzAltSky(azRad, altRad, mjd, band, rotSkyRad=numpy.pi, longRad=-1.2320792, latRad=-0.517781017, **kwargs):
    '''
    Calculate a minimal set of observing parameters give the ra, dec, and time of the observation.
    altRad -- Altitude of the boresite of the observation in radians
    azRad -- Azimuth of the boresite of the observation in radians
    mjd -- MJD of the observation
    band -- bandpass of the observation e.g. 'r'
    rotTelRad -- Rotation of the field of view relative to the North pole in radians Default=0.
    longRad -- Longitude of the observatory in radians Default=-1.2320792
    latRad -- Latitude of the observatory in radians Default=-0.517781017
    **kwargs -- The kwargs will be put in the returned dictionary overriding the default value if it exists
    '''
    raRad, decRad = _raDecFromAltAz(altRad, azRad, longRad, latRad, mjd)
    rotTelRad = _getRotTelPos(raRad, decRad, longRad, latRad, mjd, rotSkyRad)
    return makeObsParamsAzAltTel(azRad, altRad, mjd, band, rotTelRad=rotTelRad, longRad=longRad, latRad=latRad, **kwargs)


def makeObsParamsRaDecTel(raRad, decRad, mjd, band, rotTelRad=0., longRad=-1.2320792, latRad=-0.517781017, **kwargs):
    '''
    Calculate a minimal set of observing parameters give the ra, dec, and time of the observation.
    raRad -- RA of the boresite of the observation in radians
    decRad -- Dec of the boresite of the observation in radians
    mjd -- MJD of the observation
    band -- bandpass of the observation e.g. 'r'
    rotTelRad -- Rotation of the camera relative to the telescope in radians Default=0.
    longRad -- Longitude of the observatory in radians Default=-1.2320792
    latRad -- Latitude of the observatory in radians Default=-0.517781017
    **kwargs -- The kwargs will be put in the returned dictionary overriding the default value if it exists
    '''
    altRad, azRad, paRad = altAzPaFromRaDec(raRad, decRad, longRad, latRad, mjd)
    obsMd = calcObsDefaults(raRad, decRad, altRad, azRad, rotTelRad, mjd, band, longRad, latRad)
    obsMd.update(kwargs)
    return makeObservationMetadata(obsMd)


def makeObsParamsRaDecSky(raRad, decRad, mjd, band, rotSkyRad=numpy.pi, longRad=-1.2320792, latRad=-0.517781017, **kwargs):
    '''
    Calculate a minimal set of observing parameters give the ra, dec, and time of the observation.
    raRad -- RA of the boresite of the observation in radians
    decRad -- Dec of the boresite of the observation in radians
    mjd -- MJD of the observation
    band -- bandpass of the observation e.g. 'r'
    rotSkyRad -- Rotation of the field of view relative to the North pole in radians Default=0.
    longRad -- Longitude of the observatory in radians Default=-1.2320792
    latRad -- Latitude of the observatory in radians Default=-0.517781017
    **kwargs -- The kwargs will be put in the returned dictionary overriding the default value if it exists
    '''
    rotTelRad = _getRotTelPos(raRad, decRad, longRad, latRad, mjd, rotSkyRad)
    return makeObsParamsRaDecTel(raRad, decRad, mjd, band, rotTelRad=rotTelRad, longRad=longRad, latRad=latRad, **kwargs)


def arcsecFromRadians(value):
    """
    Convert an angle in radians to arcseconds

    Note: if you input None, you will get None back
    """
    if value is None:
        return None

    return 3600.0*numpy.degrees(value)


def radiansFromArcsec(value):
    """
    Convert an angle in arcseconds to radians

    Note: if you input None, you will get None back
    """
    if value is None:
        return None

    return numpy.radians(value/3600.0)


def arcsecFromDegrees(value):
    """
    Convert an angle in degrees to arcseconds

    Note: if you input None, you will get None back
    """
    if value is None:
        return None

    return 3600.0*value


def degreesFromArcsec(value):
    """
    Convert an angle in arcseconds to degrees

    Note: if you input None, you will get None back
    """
    if value is None:
        return None

    return value/3600.0
