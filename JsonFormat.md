# JSON Protocol Specification & Message Format

> เอกสารอ้างอิงโครงสร้าง JSON Message, รายการ Action, ฟิลด์ TimeStamp และ Payload ทั้งหมดที่ใช้สื่อสารระหว่าง Client และ Server ผ่าน TCP Socket

---

## 1. ภาพรวมโปรโตคอล (Protocol Overview & Framing)

การสื่อสารระหว่าง Client และ Server ในโปรเจกต์นี้ทำงานบน **TCP Stream Socket (`SOCK_STREAM`)** โดยมีข้อตกลงระดับ Application Layer ดังนี้:

1. **Serialization:** ข้อความทั้งหมดถูกแปลงเป็น **JSON UTF-8 string** บรรทัดเดียว
2. **Delimiter Framing (`\n`):** ทุกแพ็กเก็ตจะต้องปิดท้ายด้วย `\n` (Newline) เสมอ เพื่อแก้ปัญหา **TCP Packet Boundary (Sticky Packets / Packet Fragmentation)** ทำให้ฝั่งรับสามารถแยกข้อความแต่ละอันออกจากกันได้อย่างแม่นยำ
3. **โครงสร้างซองจดหมายหลัก (Standard 3-Key Envelope):**
   ```json
   {
     "type": "<ACTION_NAME>",
     "timestamp": "HH:MM:SS",
     "payload": { ... }
   }
   ```

### รายละเอียดฟิลด์หลัก 3 คีย์
| ฟิลด์ | ชนิดข้อมูล | คำอธิบาย |
| :--- | :--- | :--- |
| `type` | `String` | ชื่อ Action หรือคำสั่ง เพื่อบอกให้ตัวประมวลผลรู้ว่าจะนำ `payload` ไปทำอะไร |
| `timestamp` | `String` | เวลาที่ส่งข้อความ (Format: `HH:MM:SS`) ใช้สำหรับบันทึก Log และแสดงเวลาเรียงลำดับในห้องแชท |
| `payload` | `Object` | ข้อมูลจำเพาะ (Parameters) ของแต่ละ Action |

---

## 2. Fundamental Actions (Part 2: R3 – R11)

### 2.1 Identity & User Directory (การลงทะเบียนและรายชื่อออนไลน์)

---

#### 🔹 `REGISTER`
* **ทิศทาง:** Client ➔ Server
* **วัตถุประสงค์:** ส่งชื่อ Username ที่ต้องการใช้ เพื่อให้ Server ตรวจสอบว่าซ้ำกับผู้อื่นหรือไม่ (**R3**)
* **คำอธิบาย Payload:**
  * `username` (`String`): ชื่อที่ผู้ใช้ต้องการลงทะเบียน (ห้ามเว้นว่าง และต้องไม่ซ้ำกับคนที่ออนไลน์อยู่)
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "REGISTER",
    "timestamp": "14:00:01",
    "payload": {
      "username": "Alice"
    }
  }
  ```

---

#### 🔹 `REGISTER_ACK`
* **ทิศทาง:** Server ➔ Client
* **วัตถุประสงค์:** ตอบกลับผลการลงทะเบียนชื่อว่าผ่านหรือไม่
* **คำอธิบาย Payload:**
  * `success` (`Boolean`): `true` หากลงทะเบียนสำเร็จ, `false` หากชื่อซ้ำหรือไม่ถูกต้อง
  * `message` (`String`): ข้อความอธิบายผลลัพธ์ เช่น `"Username accepted"` หรือเหตุผลที่ปฏิเสธ
* **ตัวอย่างข้อความ (สำเร็จ):**
  ```json
  {
    "type": "REGISTER_ACK",
    "timestamp": "14:00:01",
    "payload": {
      "success": true,
      "message": "Username accepted"
    }
  }
  ```
* **ตัวอย่างข้อความ (ไม่สำเร็จ - ชื่อซ้ำ):**
  ```json
  {
    "type": "REGISTER_ACK",
    "timestamp": "14:00:01",
    "payload": {
      "success": false,
      "message": "Username already taken"
    }
  }
  ```

---

#### 🔹 `CLIENT_LIST`
* **ทิศทาง:** Server ➔ All Clients (Broadcast)
* **วัตถุประสงค์:** แจกแจงรายชื่อผู้ใช้ที่กำลังเชื่อมต่ออยู่ในระบบทุกคน รวมทั้งชื่อของตัวเอง (**R4**) โดย Server จะส่งแพ็กเก็ตนี้อัตโนมัติทุกครั้งที่มีคน Login เข้ามาใหม่ หรือมีคน Disconnect ออกไป
* **คำอธิบาย Payload:**
  * `clients` (`Array of Strings`): รายการชื่อผู้ใช้งานทุกคนที่กำลังออนไลน์อยู่
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "CLIENT_LIST",
    "timestamp": "14:00:02",
    "payload": {
      "clients": ["Alice", "Bob", "Charlie"]
    }
  }
  ```

---

### 2.2 Private Messaging (แชทส่วนตัว 1-on-1)

---

#### 🔹 `PRIVATE_MSG`
* **ทิศทาง:** 
  1. Client ➔ Server (ผู้ส่งส่งหาเป้าหมาย)
  2. Server ➔ ผู้รับ (Unicast) และ Server ➔ ผู้ส่ง (Echo สำเนา)
* **วัตถุประสงค์:** ส่งข้อความแชทคุยส่วนตัวแบบตัวต่อตัว มีเฉพาะผู้ส่งและผู้รับเท่านั้นที่เห็นข้อความ (**R7**)
* **คำอธิบาย Payload:**
  * `to` (`String`): ชื่อผู้รับปลายทาง
  * `from` (`String`, Server เติมให้อัตโนมัติ): ชื่อของผู้ส่งข้อความ
  * `text` (`String`): เนื้อหาข้อความแชท
* **ตัวอย่างข้อความ (Client ส่งให้ Server):**
  ```json
  {
    "type": "PRIVATE_MSG",
    "timestamp": "14:01:10",
    "payload": {
      "to": "Bob",
      "text": "สวัสดี Bob ว่างคุยไหม"
    }
  }
  ```
* **ตัวอย่างข้อความ (Server ส่งต่อให้ Bob และส่งสำเนาสะท้อนให้ Alice):**
  ```json
  {
    "type": "PRIVATE_MSG",
    "timestamp": "14:01:10",
    "payload": {
      "from": "Alice",
      "to": "Bob",
      "text": "สวัสดี Bob ว่างคุยไหม"
    }
  }
  ```

---

### 2.3 Group Management & Messaging (การจัดการกลุ่มและแชทกลุ่ม)

---

#### 🔹 `CREATE_GROUP`
* **ทิศทาง:** Client ➔ Server
* **วัตถุประสงค์:** ขอเปิดห้องแชทกลุ่มใหม่ โดยมีผู้สร้างเป็นสมาชิกเริ่มต้นเพียงคนเดียว (**R8**)
* **คำอธิบาย Payload:**
  * `group` (`String`): ชื่อกลุ่มที่ต้องการสร้าง (ต้องไม่ซ้ำกับกลุ่มเดิมที่มีอยู่)
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "CREATE_GROUP",
    "timestamp": "14:02:00",
    "payload": {
      "group": "StudyRoom"
    }
  }
  ```

---

#### 🔹 `GROUP_LIST`
* **ทิศทาง:** Server ➔ All Clients (Broadcast)
* **วัตถุประสงค์:** แจ้งรายการกลุ่มทั้งหมดที่มีอยู่ในระบบ พร้อมรายชื่อสมาชิกในแต่ละกลุ่ม ให้ทุก Client ได้เห็น (**R9**)
* **คำอธิบาย Payload:**
  * `groups` (`Object / Key-Value`): โดย Key คือชื่อกลุ่ม และ Value คือ Array รายชื่อสมาชิกในกลุ่มนั้น
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "GROUP_LIST",
    "timestamp": "14:02:01",
    "payload": {
      "groups": {
        "StudyRoom": ["Alice"],
        "GamingRoom": ["Bob", "Charlie"]
      }
    }
  }
  ```

---

#### 🔹 `JOIN_GROUP`
* **ทิศทาง:** Client ➔ Server
* **วัตถุประสงค์:** ผู้ใช้กดขอเข้าร่วมกลุ่มด้วยความสมัครใจของตนเอง ไม่ถูกดึงเข้ากลุ่มอัตโนมัติ (**R10**)
* **คำอธิบาย Payload:**
  * `group` (`String`): ชื่อกลุ่มที่ต้องการกดเข้าร่วม
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "JOIN_GROUP",
    "timestamp": "14:02:30",
    "payload": {
      "group": "StudyRoom"
    }
  }
  ```

---

#### 🔹 `GROUP_MSG`
* **ทิศทาง:**
  1. Client ➔ Server (ส่งข้อความเข้าห้องกลุ่ม)
  2. Server ➔ สมาชิกทุกคนในห้องกลุ่ม (Multicast เฉพาะคนที่ Join แล้ว)
* **วัตถุประสงค์:** ส่งข้อความพูดคุยในกลุ่ม โดยจะเห็นเฉพาะคนที่อยู่ในกลุ่มนั้นเท่านั้น (**R11**)
* **คำอธิบาย Payload:**
  * `group` (`String`): ชื่อห้องกลุ่มเป้าหมาย
  * `from` (`String`, Server เติมให้อัตโนมัติ): ชื่อผู้ส่งข้อความ
  * `text` (`String`): เนื้อหาข้อความแชท
* **ตัวอย่างข้อความ (Client ส่งเข้า Server):**
  ```json
  {
    "type": "GROUP_MSG",
    "timestamp": "14:03:00",
    "payload": {
      "group": "StudyRoom",
      "text": "สวัสดีทุกคนในกลุ่ม!"
    }
  }
  ```
* **ตัวอย่างข้อความ (Server Multicast กระจายให้สมาชิกในกลุ่ม):**
  ```json
  {
    "type": "GROUP_MSG",
    "timestamp": "14:03:00",
    "payload": {
      "group": "StudyRoom",
      "from": "Alice",
      "text": "สวัสดีทุกคนในกลุ่ม!"
    }
  }
  ```

---

### 2.4 Error Notification (การแจ้งเตือนข้อผิดพลาด)

---

#### 🔹 `ERROR`
* **ทิศทาง:** Server ➔ Client
* **วัตถุประสงค์:** แจ้งเตือนเมื่อ Client ส่งคำสั่งที่ผิดพลาดหรือไม่ได้รับอนุญาต
* **คำอธิบาย Payload:**
  * `code` (`String`): รหัสข้อผิดพลาดมาตรฐาน (Error Code)
  * `message` (`String`): คำอธิบายข้อผิดพลาดแบบเข้าใจง่าย
* **ตาราง Error Codes:**
  | `code` | ความหมาย |
  | :--- | :--- |
  | `USERNAME_TAKEN` | ชื่อผู้ใช้ซ้ำกับคนอื่นในระบบ |
  | `NOT_REGISTERED` | ส่งคำสั่งแชทก่อนทำการลงทะเบียนชื่อ |
  | `USER_NOT_FOUND` | ผู้รับใน `PRIVATE_MSG` ไม่ออนไลน์ |
  | `GROUP_EXISTS` | ชื่อกลุ่มที่ต้องการสร้างมีอยู่แล้ว |
  | `GROUP_NOT_FOUND` | ไม่พบกลุ่มที่ระบุ |
  | `ALREADY_IN_GROUP` | ผู้ใช้เป็นสมาชิกในกลุ่มนี้อยู่แล้ว |
  | `NOT_IN_GROUP` | พยายามส่งข้อความเข้ากลุ่มที่ตนเองยังไม่ได้กด Join |
  | `INVALID_PACKET` | รูปแบบ JSON เสียหาย หรือขาดคีย์จำเป็น |
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "ERROR",
    "timestamp": "14:03:05",
    "payload": {
      "code": "USERNAME_TAKEN",
      "message": "This username is already taken. Please pick another."
    }
  }
  ```

---

## 3. Special & Bonus Feature Actions (Part 3)

### 3.1 Real-Time Typing Indicator (Special 3)

---

#### 🔹 `TYPING`
* **ทิศทาง:**
  1. Client ➔ Server (เมื่อผู้ใช้กำลังพิมพ์ข้อความในห้องแชท)
  2. Server ➔ สมาชิกคนอื่นในห้องนั้น (ไม่สะท้อนกลับหาตัวเอง)
* **วัตถุประสงค์:** แสดงสถานะ `"กำลังพิมพ์..."` ในห้องแชทส่วนตัวหรือห้องแชทกลุ่มแบบ Real-time พร้อมกลไก Debounce 3 วินาที
* **คำอธิบาย Payload:**
  * `room_type` (`String`): ชนิดห้องแชท (`"PRIVATE"` หรือ `"GROUP"`)
  * `target` (`String`): ปลายทาง (หากเป็น PRIVATE จะเป็นชื่อเพื่อน, หากเป็น GROUP จะเป็นชื่อกลุ่ม)
  * `from` (`String`, Server เติมให้): ชื่อคนที่กำลังพิมพ์
  * `is_typing` (`Boolean`): `true` เมื่อเริ่มพิมพ์, `false` เมื่อหยุดพิมพ์หรือกดส่งแล้ว
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "TYPING",
    "timestamp": "14:04:00",
    "payload": {
      "room_type": "GROUP",
      "target": "StudyRoom",
      "from": "Alice",
      "is_typing": true
    }
  }
  ```

---

### 3.2 AI Conversation Summarization (Special 1: AI Feature)

---

#### 🔹 `AI_SUMMARY_REQ`
* **ทิศทาง:** Client ➔ Server
* **วัตถุประสงค์:** ร้องขอให้ Server นำประวัติการคุยในห้องแชทนั้นส่งไปให้ AI Model (เช่น Gemini API) เพื่อทำการสรุปประเด็นสำคัญ
* **คำอธิบาย Payload:**
  * `room_type` (`String`): `"PRIVATE"` หรือ `"GROUP"`
  * `target` (`String`): ชื่อเพื่อน หรือ ชื่อกลุ่ม
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "AI_SUMMARY_REQ",
    "timestamp": "14:05:00",
    "payload": {
      "room_type": "GROUP",
      "target": "StudyRoom"
    }
  }
  ```

---

#### 🔹 `AI_SUMMARY_RES`
* **ทิศทาง:** Server ➔ Room Members
* **วัตถุประสงค์:** กระจายผลสรุปข้อความแชทจาก AI ให้ทุกคนในห้องได้รับทราบ
* **คำอธิบาย Payload:**
  * `room_type` (`String`): `"PRIVATE"` หรือ `"GROUP"`
  * `target` (`String`): ชื่อห้องหรือผู้ใช้
  * `requested_by` (`String`): ชื่อผู้ใช้ที่กดปุ่มขอสรุป
  * `summary` (`String`): เนื้อหาสรุปสาระสำคัญที่ได้รับจาก AI Model
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "AI_SUMMARY_RES",
    "timestamp": "14:05:03",
    "payload": {
      "room_type": "GROUP",
      "target": "StudyRoom",
      "requested_by": "Alice",
      "summary": "สรุปสาระสำคัญ:\n1. ตกลงทำ Socket Chat ด้วย Python\n2. กำหนดนัดส่งงานสัปดาห์หน้า"
    }
  }
  ```

---

### 3.3 Voice Message Clips (Special 4)

---

#### 🔹 `VOICE_MSG`
* **ทิศทาง:**
  1. Client ➔ Server (ผู้ส่งอัดเสียงเสร็จแล้วแปลงเป็น Base64 ส่งเข้ามา)
  2. Server ➔ ผู้รับ (กรณีแชทเดี่ยว) หรือ สมาชิกทุกคน (กรณีแชทกลุ่ม)
* **วัตถุประสงค์:** ส่งคลิปเสียงสั้น (Push-to-Talk) ในรูปแบบไฟล์เสียง WAV ที่เข้ารหัสเป็น Base64
* **คำอธิบาย Payload:**
  * `room_type` (`String`): `"PRIVATE"` หรือ `"GROUP"`
  * `target` (`String`): ผู้รับ หรือ กลุ่มเป้าหมาย
  * `from` (`String`, Server เติมให้): ชื่อผู้ส่งคลิปเสียง
  * `audio_b64` (`String`): ข้อมูลไบนารีของไฟล์เสียง `.wav` ในรูปแบบ Base64 string
  * `duration` (`Float`): ความยาวของคลิปเสียงเป็นวินาที (เช่น `2.5`)
* **ตัวอย่างข้อความ:**
  ```json
  {
    "type": "VOICE_MSG",
    "timestamp": "14:06:10",
    "payload": {
      "room_type": "GROUP",
      "target": "StudyRoom",
      "from": "Alice",
      "audio_b64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
      "duration": 2.5
    }
  }
  ```

---

## 4. ตารางสรุป Action ทั้งหมด (Master Quick Reference)

| Action (`type`) | ทิศทาง | Mapped Req | สรุปหน้าที่สั้นๆ | คีย์สำคัญใน Payload |
| :--- | :--- | :--- | :--- | :--- |
| `REGISTER` | Client ➔ Server | **R3** | ขอลงทะเบียนชื่อผู้ใช้ | `username` |
| `REGISTER_ACK` | Server ➔ Client | **R3** | ตอบผลการตรวจชื่อซ้ำ | `success`, `message` |
| `CLIENT_LIST` | Server ➔ All | **R4** | ส่งรายชื่อคนออนไลน์ทุกคน | `clients` |
| `PRIVATE_MSG` | Client ➔ Srv ➔ Client | **R5, R6, R7** | ส่งข้อความแชทส่วนตัว 1-to-1 | `from`, `to`, `text` |
| `CREATE_GROUP` | Client ➔ Server | **R8** | สร้างห้องกลุ่มใหม่ (มีตัวเองคนแรก) | `group` |
| `GROUP_LIST` | Server ➔ All | **R9** | แจกแจงรายชื่อกลุ่มพร้อมสมาชิก | `groups` |
| `JOIN_GROUP` | Client ➔ Server | **R10** | ขอเข้ากลุ่มด้วยตนเอง | `group` |
| `GROUP_MSG` | Client ➔ Srv ➔ Group | **R5, R6, R11** | ส่งข้อความคุยในกลุ่ม | `group`, `from`, `text` |
| `ERROR` | Server ➔ Client | General | แจ้งเตือนข้อผิดพลาด | `code`, `message` |
| `TYPING` | Client ➔ Srv ➔ Room | **Special 3** | แจ้งสถานะกำลังพิมพ์ | `room_type`, `target`, `from`, `is_typing` |
| `AI_SUMMARY_REQ`| Client ➔ Server | **Special 1** | ขอให้ AI สรุปแชทในห้อง | `room_type`, `target` |
| `AI_SUMMARY_RES`| Server ➔ Room | **Special 1** | รับผลสรุปแชทจาก AI | `room_type`, `target`, `summary` |
| `VOICE_MSG` | Client ➔ Srv ➔ Room | **Special 4** | ส่งคลิปเสียงสั้น Base64 | `room_type`, `target`, `audio_b64`, `duration` |
