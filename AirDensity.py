
# coding: utf-8

# # Calculate Air Density for a time and place in the past
# 
# Refer to AirDensity.pybb notebook: air density function that takes pressure and temperature, together with either dew point on relative humidity. 

# # Calculate Air Density
# Source : https://wahiduddin.net/calc/density_altitude.htm#b15 <br>
# First try compare the two models to calculate saturation vapour pressure, Es, at temperature T. 


# ## Create a function
# Note that at dew point the vapour pressure of water equals the saturation vapour pressure Es = Vp. This is where relative humidity, hum, is 100%, because relative humidity is defined as Pv / Es. This means it is straightforward for the function to use relative humidity if the dew point temperature is not avaiable, or, if neither is supplied, assume that the relative humidity is 80%, which is around average for the UK. Finally adjust publisehd sea level for elevation

def rhoCalc(Pressure=1020, Temp=15, DP=False, Humidity=False, Elevation=0):
    """ Takes pressure P in millibars (so multiply by 100 to get Pascals)
    ambient temperature T and dew point DP in degrees C and/or relative humidity where 80% entered as 80
    and elevation  in m
    Returns air density in kg/m^3 """ 
    Rd = 287.05  #J/(kg*degK)
    Rv = 461.495 #J/(kg*degK)
    c10 = 6.1078
    c11 = 7.5
    c12 = 237.3
    g =  9.80665   # gravitational constant, m/sec^2
    M = 28.9644/1000    # molecular weight of dry air, kg/mol
    L =  6.5/1000  # temperature lapse rate, deg K/m
    R = 8.31432    # gas constant, J/ (mol*deg K) 
    Es = 100 * c10 * 10 **(c11*Temp/(c12+Temp))   # Saturation Vapour Pressure in kg/m^3
    if not(isinstance(DP,bool)):
        Pv = 100 * c10 * 10 **(c11*DP/(c12+DP)) # Vapour pressure at dew point in kg/m^3
    elif not(isinstance(Humidity,bool)):
        if Humidity > 1: Humidity /= 100
        Pv = Humidity * Es      # relativeHumidity is defined as Pv / Es
    else:
        Pv = 0.8 * Es      # Average relative humidity in the UK is 80%
    TempK = Temp + 273.15
    localP = Pressure * 100 * (TempK / (TempK + L * Elevation)) ** (g*M/(R*L)) # multiply 100 for kg/m^3 and adjust for elevation
    
    airDensity =  localP  / Rd / TempK * (1-Pv/localP*(1-Rd/Rv))
    return airDensity
