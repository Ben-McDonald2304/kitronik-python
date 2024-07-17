# Python library for Kitronik Air Quality Sensor
## BME688
### Initialisation
To first use the sensor, you must initialise it. This allows you to take temperature, humidity and pressure readings.
```
init_sensor()
```
To take gas sensor readings, the gas sensor must be initialised separately.
```
init_gas_sensor()
```
To get a more accurate reading off of the gas sensor, it must have some baseline values. The baseline values should be done in a well ventilated area and takes approximately 5 minutes.

This is not necessarily needed, it just improves the accuracy of the readings.
```
establish_baselines()
```
### Taking readings
To take the readings off the sensor use the function:
```
read_data_registers()
```
You can now call the calc functions, which returns the true value of the readings.
```
temperature = calc_temperature()
humidity = calc_humidity()
pressure = calc_pressure()
iaqScore, iaqPercent, eCO2Value = read_air_quality()
```
## OLED Screen
### initialisation
Only one function is needed for initialisation of the screen.
```
init_display()
```
### Showing text
Then after to show any text:
```
show(textToShow, lineNumber)
```
For example:
```
show("Hello World", 0)
```
Do note that, if your string is too long to fit on the line, it will be cut off.
