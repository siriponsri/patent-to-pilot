# Data boundary — HealthTech

ข้อมูลหลักที่วางแผนใช้คือ Bridge-MedDevKG ภายใต้สิทธิ์/cohort ที่ยังต้องคลี่คลาย, SciFact สำหรับ evidence component และ official device/product records ดู [data registry](../configs/healthtech/data_registry.json)

รอบ migration ไม่ได้ดาวน์โหลด Bridge/SciFact payload หรือเผยแพร่ third-party raw data ตัวอย่างที่นำเข้า Git อยู่ใน `examples/healthtech/synthetic-device/` เป็นข้อความและรหัสที่ผู้พัฒนาแต่งขึ้นทั้งหมด

G03 manifests เก็บข้อเท็จจริงการดาวน์โหลดเดิม ไม่ใช่คำสั่งให้ใช้ PLS/EnterpriseRAG เป็น HealthTech benchmark ดู [history/cleanup](../docs/healthtech/HISTORY.md) ก่อนใช้ local raw files หรือกู้คืนไฟล์ที่ลบแบบ recoverable แล้ว ผล historical tests ไม่กลายเป็น scientific HealthTech evidence

Raw/processed/derived payloads, evaluator-only labels และ credentials ยังคงถูกกันจาก Git สิทธิ์ MIT ของ repository code ไม่ได้ยืนยันสิทธิ์ data/release assets และ paper license ไม่ขยายสิทธิ์ dataset
