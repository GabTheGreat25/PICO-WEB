import network
import socket
import utime
import machine
from imu import MPU6050

ssid = 'YOUR_SSID_HERE'
password = 'YOUR_PASSWORD_HERE' 

# Water Sensor Configuration
WATER_SENSOR_PIN = 17
water_sensor = machine.Pin(WATER_SENSOR_PIN, machine.Pin.IN)

# Buzzer Configuration
BUZZER_PIN = 16
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)

# Ultrasonic Sensor Configuration
TRIGGER_PIN = 13
ECHO_PIN = 12
trigger = machine.Pin(TRIGGER_PIN, machine.Pin.OUT)
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)

# Vibration Motor Configuration
MOTOR_PIN = 15
vibration_motor = machine.Pin(MOTOR_PIN, machine.Pin.OUT)

# MPU6050 Configuration
i2c = machine.I2C(0, sda=machine.Pin(4), scl=machine.Pin(5), freq=400000)
imu = MPU6050(i2c)

def connect():
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        utime.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

def ultrasonic_distance():
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

    if 1 <= distance <= 5:
        distance_category = 'Very Close'
        activate_vibration_motor()
    elif 6 <= distance <= 10:
        distance_category = 'Getting Near'
        activate_vibration_motor()
    elif 11 <= distance <= 15:
        distance_category = 'There is an Object'
        activate_vibration_motor()
    else:
        distance_category = 'Out of Range'
        deactivate_vibration_motor()

    return distance_category

def activate_vibration_motor():
    vibration_motor.value(1)

def deactivate_vibration_motor():
    vibration_motor.value(0)

def webpage(water_state, buzzer_state, ultrasonic_category, vibration_status, stick_state):
    # Template HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="1">
    <style>
        body {{
            font-family: "Arial", sans-serif;
            text-align: center;
            background-color: #f7f7f7;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }}
        .parallax {{
            background-image: url("https://i.ytimg.com/vi/EWsMnA1-MTw/maxresdefault.jpg");
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-size: cover;
            height: 100vh;
        }}
        .container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            flex-direction: column;
            position: relative;
            z-index: 1;
        }}
        .card {{
            background-color: #ffffff;
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 20px;
            width: 60%;
            margin-top: 20px;
        }}
        h1 {{
            color: #222;
        }}
        p {{
            color: #555;
            margin-bottom: 20px;
            font-size: 18px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
        }}
        th {{
            background-color: #f3f3f3;
            color: #555;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f7f7f7;
        }}
    </style>
            </head>
            <body>
            <div class="parallax"></div>
            <div class="container">
            <h1>Welcome to Smart Blind Stick</h1>
            <p>Experience the future of navigation for the visually impaired. Our Smart Blind Stick integrates cutting-edge sensors and technology to provide real-time data for enhanced safety and independence.</p>
             <div class="card">
                <h2>Sensor Data</h2>
                <table>
                <tr>
                    <th>Sensor</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Ultra Sonic</td>
                    <td>{ultrasonic_category}</td>
                </tr>
                <tr>
                    <td>Water Sensor</td>
                    <td>{water_state}</td>
                </tr>
                <tr>
                    <td>Gyro</td>
                    <td>{stick_state}</td>
                </tr>
                <tr>
                    <td>Buzzer</td>
                    <td>{buzzer_state}</td>
                </tr>
                <tr>
                    <td>Vibration Sensor</td>
                    <td>{vibration_status}</td>
                </tr>
                </table>
            </div>
            </body>
            </html>
            """
    return str(html)

def serve(connection):
    # Start a web server
    buzzer_state = 'Deactivated'
    vibration_status = 'Stopped'
    stick_state = 'Normal'
    
    while True:
        client = connection.accept()[0]
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass

        water_detected = water_sensor.value()
        if water_detected:
            water_state = 'Water Detected'
            buzzer_state = 'Activated'
            buzzer.on()  # Activate the buzzer when water is detected
        else:
            water_state = 'No Water Detected'
            buzzer_state = 'Deactivated'
            buzzer.off()  # Deactivate the buzzer when no water is detected

        ultrasonic_category = ultrasonic_distance()
        if vibration_motor.value():
            vibration_status = 'Running'
        else:
            vibration_status = 'Stopped'

        # Check stick orientation
        gx = round(imu.gyro.x)
        gy = round(imu.gyro.y)
        gz = round(imu.gyro.z)
        angle = gx * 0.4

        if abs(angle) > 10:
            stick_state = 'Dropped'
            buzzer_state = 'Activated'
            if not buzzer.value():
                buzzer.on()
                utime.sleep(3)
                buzzer.off()
        else:
            stick_state = 'Normal'
            if not water_detected:  # Turn off the buzzer if the stick is not dropped and no water is detected
                buzzer.off()
                buzzer_state = 'Deactivated'

        html = webpage(water_state, buzzer_state, ultrasonic_category, vibration_status, stick_state)
        client.send(html)
        client.close()

try:
    ip = connect()
    connection = open_socket(ip)
    serve(connection)
except KeyboardInterrupt:
    machine.reset()
