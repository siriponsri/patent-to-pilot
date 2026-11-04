# Next actions — requirements before execution

1. Parentใช้สองresource snapshotsประกอบmodel research/บริบทแชตต้นฉบับ อย่าใช้free GPUเป็นallocation ไม่มีcomputeauthorityจากpreflightนี้
2. ระบุPatEmbed modelrepository+immutable revision/checkpointจริง หรือขอreferenceจากownerเมื่อแชตและrepoยังไม่ยืนยัน ไม่renameMiniLMเป็นPatEmbed
3. เก็บrequirementsที่ยังไม่แน่ใจเป็นชุดเดียว: approvedGPUUUIDหรือCPUquotaและwindow/deadline/shared-serviceconstraints, isolatedruntime/setupหรือexistingenvpath, model/data license/useและdownload/diskbounds, paidproviderbudgetscopeเฉพาะส่วนที่จะใช้จริง ไม่ให้ownerเลือกimplementationdetailsทุกข้อ
4. เมื่อscopeและสิทธิ์ชัด ค่อยออกlong-runGoalใหม่พร้อมexactmodel/backendcontract, resumableshards/localimport/sharedretrieval+dossiers และmeaningfulmetrics ใช้latestcode/repairworktreeจริง ไม่silentlydiscardvectorcrash/resumefixesที่ยังแยกbranch
5. ต้องตรวจsnapshot/capacityอีกครั้งตอนเริ่มjobภายใต้allocationนั้น เพราะรายงานนี้เป็นจุดเวลา ไม่เริ่มcompute/download/installหรือเปลี่ยนsettingsจากเอกสารนี้

สถานะ: read-onlyresourcepreflight COMPLETE; allocation UNKNOWN_NOT_GRANTED; model runtime/compatibility NOT_TESTED; PatEmbedexactcheckpoint NOT_FOUND_IN_INSPECTED_SCOPE; remoteembedding NOT_RUN
