const express = require("express");
const mysql = require("mysql");
const cors = require("cors");

const app = express();
const PORT = 3000;

// เปิดใช้งาน CORS
app.use(cors());

// สร้างการเชื่อมต่อกับฐานข้อมูล
const db = mysql.createConnection({
  host: "192.168.231.250", // ใส่ ip Rasberry pi
  user: "root", // ชื่อผู้ใช้ฐานข้อมูล
  password: "123456", // รหัสผ่านฐานข้อมูล (ถ้าไม่มีให้เว้นว่าง)
  database: "Pigeon_Data", // ชื่อฐานข้อมูล
});

// เชื่อมต่อฐานข้อมูล
db.connect((err) => {
  if (err) {
    console.error("Database connection failed:", err);
  } else {
    console.log("Connected to the database.");
  }
});


// สร้าง API สำหรับดึงข้อมูลการตรวจจับ
app.get("/detections", (req, res) => {
  const query = "SELECT * FROM bird_detection_logs ORDER BY id DESC";
  db.query(query, (err, results) => {
    if (err) {
      console.error("Error fetching data:", err);
      res.status(500).send("Error fetching data");
    } else {
      console.log("Fetched data:", results); // ตรวจสอบข้อมูลที่ได้รับ
      res.json(results);
    }
  });
});

app.get("/check-db", (req, res) => {
  db.connect((err) => {
    if (err) {
      res.json({ status: "disconnected" });
    } else {
      res.json({ status: "connected" });
    }
  });
});

// เริ่มเซิร์ฟเวอร์
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});