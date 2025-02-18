from ultralytics import YOLO  # type: ignore
import cv2
import mysql.connector
from datetime import datetime
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time

# กำหนด Pin Relay
RELAY_PIN = 17  
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.LOW)  # ปิด Relay เริ่มต้น

# เชื่อมต่อกับฐานข้อมูล
db = mysql.connector.connect(
    host="localhost", 
    user="root",   
    password="123456", 
    database="Pigeon_Data"  
)

if db.is_connected():
    print("เชื่อมต่อฐานข้อมูลสำเร็จ")
else:
    print("ไม่สามารถเชื่อมต่อฐานข้อมูล")

cursor = db.cursor()

# โหลดโมเดล YOLO
model = YOLO("/home/pi/project/runs/detect/train3/weights/models.pt")

# เปิดกล้อง
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
cap.set(cv2.CAP_PROP_AUTOFOCUsS, 0) 
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  
cap.set(cv2.CAP_PROP_FOCUS, 10)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

# ตัวแปรเก็บสถานะของ Relay
relay_status = False  # เริ่มต้น Relay เป็นปิด

# ฟังก์ชั่นเชื่อมต่อ MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("เชื่อมต่อ EMQX Broker สำเร็จ")
        client.subscribe("speaker/manual")
    else:
        print(f"เชื่อมต่อ EMQX Broker ล้มเหลว รหัส: {rc}")

def on_message(client, userdata, msg):
    global relay_status
    message = msg.payload.decode().strip()
    print(f"ข้อความจาก MQTT: {msg.topic} -> {message}")

    if message == "1":
        GPIO.output(RELAY_PIN, GPIO.HIGH)
        relay_status = True  # ปรับสถานะ Relay เป็นเปิด
        print("เปิด Relay")
        
    elif message == "0":
        GPIO.output(RELAY_PIN, GPIO.LOW)
        relay_status = False  # ปรับสถานะ Relay เป็นปิด
        print("ปิด Relay")
        
    else:
        print("ข้อความไม่ถูกต้อง")

client = mqtt.Client()
client.username_pw_set("pi", "nattawut3101.") # username, password emqx
client.on_connect = on_connect
client.on_message = on_message

# เชื่อมต่อ MQTT Broker
BROKER = "192.168.231.250" # ip raspberry pi
PORT = 1883

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("ไม่สามารถเปิดกล้องได้")
            break

        # ตรวจจับวัตถุโดยใช้ YOLO
        results = model.predict(frame, conf=0.5, save=False)
        detected = False  # เริ่มต้นการตรวจจับเป็น False

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
            label = model.names[int(box.cls)]  
            conf = box.conf[0].cpu().numpy()  

            print(f"พบวัตถุ: {label}, ความมั่นใจ: {conf:.2f}")

            if label.lower() in ["bird", "pigeon"]:
                detected = True  # พบการตรวจจับนกแล้ว
                # if not relay_status:  # ตรวจสอบสถานะ Relay ก่อน
                GPIO.output(RELAY_PIN, GPIO.HIGH)  # เปิด Relay เมื่อพบการตรวจจับนก
                relay_status = True
                print("เปิด Relay เนื่องจากตรวจจับนก")
                
                detection_date = datetime.now().date()  
                detection_time = datetime.now().time()  
                status = f"{label} detected"  

                try:
                    sql = """
                    INSERT INTO bird_detection_logs (detection_date, detection_time, status)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql, (detection_date, detection_time, status))
                    db.commit()  
                    print(f"บันทึกการตรวจจับ: วันที่ {detection_date}, เวลา {detection_time}, สถานะ: {status}")
                except mysql.connector.Error as err:
                    print(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {err}")

            frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            frame = cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # ถ้าไม่พบการตรวจจับนกในทุกๆ รอบการตรวจจับ
        if not detected:
            GPIO.output(RELAY_PIN, GPIO.LOW)  # ปิด Relay เมื่อไม่พบการตรวจจับนกและ Relay ยังไม่ได้เปิดจาก MQTT
            print("ปิด Relay เนื่องจากไม่พบการตรวจจับนก")

        # แสดงผล
        status_text = "Bird Detected!" if detected else "No Detection"
        frame = cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # แสดงหน้าต่างผลการตรวจจับ
        cv2.imshow("YOLOv8 Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("หยุดโปรแกรม")
except Exception as e:
    print(f"เกิดข้อผิดพลาด: {e}")
finally:
    GPIO.cleanup()

# ปิดกล้องและฐานข้อมูล
cap.release()
db.close()
cv2.destroyAllWindows()
