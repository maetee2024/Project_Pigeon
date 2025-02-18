<template>
  <v-container class="main-container" fluid>
    <v-row>
        <v-col cols="12" class="text-center" style="padding-left: 145px; padding-right: 145px;">
          <v-card elevation="12" class="pa-6 card-blur">
            <v-card-title class="headline">📊 Dashboard</v-card-title>
          </v-card>
        </v-col>
    </v-row>

  <v-row align="center">
  <!-- Speaker Control -->
  <v-col cols="12" md="6" style="padding-left: 16px; padding-right: 16px;">
    <v-card elevation="12" class="pa-6 text-center card-blur" style="margin-left: 125px;">
      <v-card-title class="headline">🔊 Speaker Control</v-card-title>
      <v-card-text>
        <v-col cols="auto" class="d-flex justify-center">
          <v-switch
            v-model="isSpeakerOn"
            :label="isSpeakerOn ? 'Turn On' : 'Turn Off'"
            color="deep-orange darken-2"
            class="custom-switch"
            @change="handleSpeakerToggle"
          ></v-switch>
        </v-col>
        <v-chip :color="isSpeakerOn ? 'green darken-2' : 'red darken-2'" label class="mt-3 status-chip">
          {{ isSpeakerOn ? '🔊 Speaker On' : '🔇 Speaker Off' }}
        </v-chip>
      </v-card-text>
    </v-card>
  </v-col>

  <!-- System Status -->
  <v-col cols="12" md="6" style="padding-left: 16px; padding-right: 16px;">
    <v-card style="height: 265px; margin-right: 125px;" elevation="12" class="pa-6 text-center card-blur">
      <v-card-title class="headline" style="padding-top: 65px;">📡 MQTT Status</v-card-title>
      <v-card-text>
        <v-chip
          :color="mqttConnected ? 'green darken-2' : 'red darken-2'"
          label
          class="mt-3 status-chip"
        >
          {{ mqttConnected ? '🟢 Online' : '🔴 Offline' }}
        </v-chip>
      </v-card-text>
    </v-card>
  </v-col>
</v-row>

    <v-row>
      <v-col cols="12" md="10" class="mx-auto">
        <v-card elevation="12" class="pa-6 card-blur">
          <v-card-title class="headline text-center">📊 Statistics</v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-card class="stat-card blue lighten-2" elevation="6">
                  <v-card-title style="color: black; font-weight: bold;">Total Detections</v-card-title>
                  <v-card-text class="stat-text">📈 {{ totalDetections }}</v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6">
                <v-card class="stat-card deep-purple lighten-2" elevation="6">
                  <v-card-title style="color: black; font-weight: bold;">Last Detected</v-card-title>
                  <v-card-text class="stat-text">⏰ {{ lastDetected }}</v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-row>
      <v-col cols="12" md="10" class="mx-auto">
        <v-card elevation="12" class="pa-6 card-blur">
          <v-card-title class="headline text-center">📅 Detection Data</v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-data-table
              style="font-size: 20px; font-weight: bold;"
              :headers="headers"
              :items="detections"
              class="elevation-3 mt-3 rounded-table"
              :items-per-page="5"
              hide-default-footer
            >
              <template v-slot:item.detection_date="{ item }">
                <span>{{ formatDate(item.detection_date) }}</span>
              </template>
              <template v-slot:item.detection_time="{ item }">
                <span>{{ item.detection_time }}</span>
              </template>
              <template v-slot:no-data>
                <v-alert type="info">🚨 No detections available</v-alert>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>



  <script>
  import mqtt from "mqtt"; // นำเข้า mqtt library

  export default {
    data() {
      return {
        detections: [], // ข้อมูลการตรวจจับจากฐานข้อมูล
        headers: [
          { title: "ID", key: "id", props: { class: "custom-header" } },
          { title: "Detection Date", key: "detection_date", props: { class: "custom-header" } },
          { title: "Detection Time", key: "detection_time", props: { class: "custom-header" } },
          { title: "STATUS", key: "status", props: { class: "custom-header" } },
        ],

        isSpeakerOn: false, // สถานะของลำโพง
        pagination: {
          sortDesc: true,
        },
        totalDetections: 0, // จำนวนการตรวจจับทั้งหมด
        lastDetected: "N/A", // เวลาและวันที่การตรวจจับล่าสุด
        mqttClient: null, // เก็บ client ของ MQTT
        mqttConnected: false, // สถานะของ MQTT
        dbConnected: false, // สถานะของฐานข้อมูล
      };
    },
    created() {
      this.fetchDetections(); // เรียกข้อมูลเมื่อโหลดหน้าเว็บ
      this.connectMqtt(); // เชื่อมต่อกับ MQTT
    },
    methods: {
  // ฟังก์ชันดึงข้อมูลจาก API
  async fetchDetections() {
    try {
      const response = await fetch("http://192.168.231.152:3000/detections"); // ใส่ ip ของ windows
      const data = await response.json();
      console.log("Fetched detections:", data); // ตรวจสอบข้อมูลที่ได้รับ
      this.detections = data;

      // อัปเดตสถิติ
      this.totalDetections = data.length;
      if (data.length > 0) {
        const lastDetection = data[0];
        this.lastDetected = this.formatDate(lastDetection.detection_date) + ' ' + lastDetection.detection_time; // การแสดงวันที่และเวลา
      }
    } catch (error) {
      console.error("Error fetching detections:", error);
    }
  },

  async checkDatabaseConnection() {
  try {
    const response = await fetch("http://192.168.231.152:3000/check-db"); // เปลี่ยนเป็น API ที่เชื่อมต่อกับฐานข้อมูล
    if (response.ok) {
      this.dbConnected = true;
    } else {
      this.dbConnected = false;
    }
  } catch (error) {
    console.error("Error checking database connection:", error);
    this.dbConnected = false;
  }
},

  // ฟังก์ชันแปลงวันที่ให้แสดงเฉพาะวันที่
  formatDate(date) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    const formattedDate = new Date(date).toLocaleDateString('th-TH', options); 
    return formattedDate.replace(/\//g, '-'); // เปลี่ยน / เป็น -
  },

  // ฟังก์ชันเชื่อมต่อ MQTT
  connectMqtt() {
  const brokerUrl = "ws://192.168.231.250:8083/mqtt";  // IP ของ Raspberry Pi
  const options = {
    username: "pi", // ใส่ username ของ MQTT
    password: "nattawut3101.", // ใส่ password ของ MQTT
  };

  this.mqttClient = mqtt.connect(brokerUrl, options);

  this.mqttClient.on("connect", () => {
    console.log("Connected to MQTT broker");
    this.mqttConnected = true; // อัปเดตให้ขึ้น Online
  });

  this.mqttClient.on("error", (error) => {
    console.error("MQTT connection error:", error);
    this.mqttConnected = false; // ถ้าเกิด error ให้ขึ้น Offline
  });
},

  // ฟังก์ชันควบคุมการเปิด/ปิดลำโพง
  handleSpeakerToggle() {
  const topic = "speaker/manual";
  const message = this.isSpeakerOn ? "1" : "0"; // ส่ง 1 เมื่อเปิด และ 0 เมื่อปิด

  console.log(`Toggling speaker. Sending message: ${message}`);

  if (this.mqttClient && this.mqttClient.connected) {
    this.mqttClient.publish(topic, message, (error) => {
      if (error) {
        console.error("Error publishing message:", error);
      } else {
        console.log(`Published message: ${message} to topic: ${topic}`);
      }
    });
  } else {
    console.error("MQTT client not connected");
  }
 }
},
};
  </script>

<style scoped>
* {
  font-family:'Courier New', Courier, monospace;
  font-weight: bold;
}

.main-container {
  background: linear-gradient(to bottom, #2196F3, #80DEEA);
  min-height: 100vh;
  padding-bottom: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.card-blur {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}
.headline {
  font-size: 26px;
  font-weight: bold;
  color: #37474f;
}
.stat-card {
  padding: 20px;
  border-radius: 15px;
  text-align: center;
  color: white;
  transition: transform 0.3s ease;
}
.stat-card:hover {
  transform: scale(1.05);
}
.stat-text {
  font-size: 25px;
  font-weight: bold;
  color: black;
}
.rounded-table {
  border-radius: 10px;
  overflow: hidden;
}
.custom-switch {
  font-size: 25px;
  font-weight: bold;
}
.status-chip {
  font-size: 25px;
  font-weight: bold;
  padding: 10px 20px;
  border-radius: 20px;
}

.custom-header {
  font-size: 25px !important;
  font-weight: bold;
  color: #000000;
}
</style>