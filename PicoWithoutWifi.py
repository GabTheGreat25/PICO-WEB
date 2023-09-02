import machine
import utime
from imu import MPU6050

trigger = machine.Pin(13, machine.Pin.OUT)
echo = machine.Pin(12, machine.Pin.IN)
MOTOR_PIN = 15  # Change this to the actual GPIO pin number for the motor

def ultra():
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(5)
    trigger.low()

    while echo.value() == 0:
        signaloff = utime.ticks_us()
    while echo.value() == 1:
        signalon = utime.ticks_us()

    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2

    if 1 <= distance <= 20:
        print("The distance from the object is {:.2f} cm".format(distance))
        start_vibrating()
        utime.sleep(0.1)  # Pause for a short duration
    else:
        print("Out of range")
        stop_vibrating()

def start_vibrating():
    motor_pin = machine.Pin(MOTOR_PIN, machine.Pin.OUT)
    motor_pin.value(1)  # Turn on the motor

def stop_vibrating():
    motor_pin = machine.Pin(MOTOR_PIN, machine.Pin.OUT)
    motor_pin.value(0)  # Turn off the motor

def buzz(duration_ms):
    buzzer.on()
    utime.sleep_ms(duration_ms)
    buzzer.off()

# Define the GPIO pin numbers
BUZZER_PIN = 16
WATER_SENSOR_PIN = 17  # Replace with the actual GPIO pin for the water sensor

# Initialize the GPIO pins
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
water_sensor = machine.Pin(WATER_SENSOR_PIN, machine.Pin.IN)

# Create an instance of MPU6050
i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)
imu = MPU6050(i2c)

# Main loop
try:
    while True:
        ultra()
        
        # Read gyro values
        gx = round(imu.gyro.x)
        gy = round(imu.gyro.y)
        gz = round(imu.gyro.z)
        
        # Calculate the angle (slope) using gyro values for the X-axis (replace with your actual logic)
        angle = gx * 0.4  # This is a placeholder calculation, adjust based on your sensor's characteristics
        
        # Read water sensor value
        water_detected = water_sensor.value()  # Assumes HIGH when water is detected
        
        # Debug information
        print("gx", gx, "\t", "gy", gy, "\t", "gz", gz, "\t", "Angle", angle, "\t", end="\r")
    
        # Check if the angle is greater than a certain threshold or water is detected
        if abs(angle) > 10:
            print("Angle exceeds threshold. Buzzing.")
            buzz(1000)  # Buzzer buzzes for 100 ms when the angle is sloped
        
        if water_detected:
            print("Water detected. Buzzing.")
            buzz(1000)  # Buzzer buzzes for 100 ms when water is detected
        
        utime.sleep(0.1)  # Delay between distance measurements and gyro/water sensor readings

except KeyboardInterrupt:
    stop_vibrating()
    print("\nProgram stopped. Vibration stopped.")
