# Literature review — HealthTech

ชุดหลักปัจจุบันคือ HealthTech Pack วันที่ 27 ตุลาคม 2026 มี PDF 27 ฉบับ รวม 458 หน้า ตรวจ SHA-256 กับ CHECKSUMS ตรงทั้งหมดและอ่าน identity พร้อม method/task/evaluation passages ที่จำเป็น ไม่ใช่ systematic review และไม่ได้ reproduce ผลของบทความ

- [Research library / source links](../RELATED_PAPERS.md)
- [Method, dataset, evaluator และ novelty threats](healthtech/READING_NOTES.md)
- [Verified PDF identities and separate rights notes](healthtech/paper_manifest.json)
- [BibTeX](healthtech/references.bib)
- [Pack provenance](../docs/healthtech/pack-provenance.json)

Bridge-MedDevKG เป็น main task candidate แบบมีเงื่อนไข SciFact ประเมิน evidence component แยก; ChEMU/BioASQ/NLI4CT และ chemical resources เป็น supporting/extension tasks สิทธิ์ของ paper, code และ dataset ต้องตรวจแยก

PDF links ชี้ต้นทาง ไม่ bundle PDFs ใน public migration นี้ คลังเดิม 35 external PDFs กับ internal Paper 53 ยังอยู่ในเครื่องเพื่อรักษา provenance แต่ไม่ใช้เป็น research direction ปัจจุบันโดยอัตโนมัติ และไม่เพิ่ม Paper 53 ลง external bibliography

การมี quote จริงไม่ยืนยัน semantic support, feasibility, safety, FTO หรือผลตอบแทน หากใช้ LLM/NLI judges ให้รายงานเป็น exploratory proxies ตาม calibration ที่มี
