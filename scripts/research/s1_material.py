"""Original fictional source passages, user requests and independently authored answer keys.

For each case the first two passages form one documented reference and the next
two form another. This authoring file is never imported by the research runner.
"""


def family(key, lane, language, requests, answers, branches, background):
    return dict(key=key, lane=lane, language=language, requests=requests,
                answers=answers, branches=branches, background=background)


FAMILIES = [
    family("reed", "proposal", "th", [
        "ผู้ยืมเสื่อของศาลาริมบึงต้องคืนภายในกี่วัน หากยืมวันที่ 1 เมษายน 2568",
        "เสื่อที่ยืมจากศาลาริมบึงเมื่อ ๑ เมษายน ๒๕๖๘ ต้องคืนในกี่วัน",
        "ผู้ยืมเสื่อของศาลาริมบึงต้องคืนภายในกี่วัน หากยืมวันที่ 1 เมษายน 2567",
        "ระเบียบศาลาริมบึงกำหนดอัตราค่าซ่อมเสื่อไว้เท่าใด"],
        ["5 วัน", "3 วัน"], [
            ("ข้อ 2", "ตั้งแต่ 1 มกราคม 2568 การยืมเสื่อให้ใช้ระยะเวลาในใบแนบ ข แทนใบแนบ ก", "ใบแนบ ข", "รายการเสื่อมีระยะเวลายืม 5 วัน"),
            ("ข้อ 1", "ตั้งแต่ 1 มกราคม ถึง 31 ธันวาคม 2567 ผู้ยืมเสื่อต้องปฏิบัติตามใบแนบ ก", "ใบแนบ ก", "รายการเสื่อมีระยะเวลายืม 3 วัน")],
        ["การยืมกระดานเกมมีระยะเวลา 5 วัน", "จุดรับคืนเสื่อเปิดทุกวัน"]),
    family("kiln", "selection", "th", [
        "สมุดสีของห้องดินเผาต้องติดป้ายแบบใดเมื่อส่งทางไปรษณีย์",
        "ส่งสมุดสีห้องดินเผาทางไปรษณีย์ ต้องใช้ป้ายแบบไหน",
        "สมุดสีของห้องดินเผาต้องติดป้ายแบบใดเมื่อส่งด้วยตนเอง",
        "ห้องดินเผาระบุน้ำหนักสูงสุดของสมุดสีไว้เท่าใด"],
        ["ป้ายวงกลม", "ป้ายสี่เหลี่ยม"], [
            ("ข้อ 4", "สมุดสีที่ส่งทางไปรษณีย์ให้ใช้บรรจุภัณฑ์ชั้นนอกตามหัวข้อ พัสดุ", "หัวข้อ พัสดุ", "สมุดสีชนิดพัสดุให้ใช้ป้ายวงกลม"),
            ("ข้อ 7", "สมุดสีที่ผู้ทำมาส่งเองใช้หลักเกณฑ์ในหัวข้อ เคาน์เตอร์", "หัวข้อ เคาน์เตอร์", "สมุดสีที่เคาน์เตอร์ให้ใช้ป้ายสี่เหลี่ยม")],
        ["กล่องดินตัวอย่างใช้ป้ายวงกลมทั้งสองช่องทาง", "ให้เขียนชื่อผู้ส่งสมุดสีบนป้าย"]),
    family("fern", "dev", "th", [
        "บัตรนำชมสวนเฟินที่ออกวันที่ 10 มิถุนายน 2568 ให้เข้าชมได้กี่ครั้ง",
        "บัตรสวนเฟินซึ่งออกเมื่อ ๑๐ มิถุนายน ๒๕๖๘ ใช้เข้าชมได้กี่ครั้ง",
        "บัตรนำชมสวนเฟินที่ออกวันที่ 10 พฤษภาคม 2568 ให้เข้าชมได้กี่ครั้ง",
        "บัตรสวนเฟินใช้กับรถรับส่งได้กี่เที่ยว"],
        ["4 ครั้ง", "2 ครั้ง"], [
            ("ข้อแก้ไข 1", "บัตรนำชมที่ออกตั้งแต่วันที่ 1 มิถุนายน 2568 ให้ใช้บัญชีใหม่ แทนบัญชีเดิม", "บัญชีใหม่", "สำหรับบัตรนำชม สวนเฟินอนุญาตให้เข้าชม 4 ครั้ง"),
            ("ข้อ 3", "บัตรนำชมที่ออกในเดือนมกราคมถึงพฤษภาคม 2568 ให้ใช้บัญชีเดิม", "บัญชีเดิม", "สำหรับบัตรนำชม สวนเฟินอนุญาตให้เข้าชม 2 ครั้ง")],
        ["บัตรถ่ายภาพให้เข้าสวนได้ 2 ครั้ง", "เจ้าหน้าที่ลงวันออกบัตรนำชมทุกครั้ง"]),
    family("loom", "dev", "th", [
        "ผู้ใช้กี่ทอผ้าซึ่งสวมถุงมือผ้าต้องรับกุญแจที่ไหน",
        "ถ้าสวมถุงมือผ้าและจะใช้กี่ทอผ้า ต้องไปรับกุญแจจุดใด",
        "ผู้ใช้กี่ทอผ้าซึ่งสวมถุงมือยางต้องรับกุญแจที่ไหน",
        "ผู้ใช้กี่ทอผ้าทำกุญแจหายต้องเสียค่าเปลี่ยนเท่าใด"],
        ["ห้องฟ้า", "ห้องส้ม"], [
            ("ข้อยกเว้น 2", "ยกเว้นผู้ใช้กี่ที่สวมถุงมือผ้า ให้รับกุญแจตามประกาศฝ่ายผ้า", "ประกาศฝ่ายผ้า", "จุดจ่ายกุญแจกี่ของฝ่ายผ้าอยู่ที่ห้องฟ้า"),
            ("ข้อทั่วไป 1", "ผู้ใช้กี่สวมถุงมือยางให้รับกุญแจตามประกาศฝ่ายกลาง ผู้ใช้ถุงมือผ้าให้ดูข้อยกเว้น 2", "ประกาศฝ่ายกลาง", "จุดจ่ายกุญแจกี่ของฝ่ายกลางอยู่ที่ห้องส้ม")],
        ["กุญแจตู้ถุงมือผ้าเก็บในห้องส้ม", "จุดคืนกุญแจกี่อยู่คนละแห่งกับจุดจ่าย"]),
    family("bell", "dev", "th", [
        "ตามตารางหอระฆัง เครื่องทองเหลืองที่จัดแสดงกลางแจ้งต้องตรวจทุกกี่เดือน",
        "เครื่องทองเหลืองกลางแจ้งของหอระฆังมีรอบตรวจห่างกันกี่เดือน",
        "ตามตารางหอระฆัง เครื่องทองเหลืองที่จัดแสดงในร่มต้องตรวจทุกกี่เดือน",
        "หอระฆังระบุราคาตรวจเครื่องทองเหลืองครั้งละเท่าใด"],
        ["3 เดือน", "9 เดือน"], [
            ("เชิงอรรถ ก", "เครื่องที่จัดแสดงกลางแจ้งให้อ่านคอลัมน์ ลาน ในตารางวัสดุ", "ตารางวัสดุ คอลัมน์ ลาน", "แถวทองเหลือง | ลาน | รอบตรวจ 3 เดือน"),
            ("คำอธิบาย ข", "เครื่องที่จัดแสดงในร่มให้อ่านคอลัมน์ โถง ในตารางวัสดุ", "ตารางวัสดุ คอลัมน์ โถง", "แถวทองเหลือง | โถง | รอบตรวจ 9 เดือน")],
        ["แถวเหล็ก | ลาน | รอบตรวจ 9 เดือน", "แถวเหล็ก | โถง | รอบตรวจ 3 เดือน"]),
    family("fold", "proposal", "en", [
        "In the folding bookmark, which insert does the curved clip use?",
        "Which insert is specified for the bookmark's curved clip?",
        "In the folding bookmark, which insert does the straight clip use?",
        "What tensile rating is specified for the bookmark insert?"],
        ["felt", "cork"], [
            ("Claim 2", "The curved clip of claim 1 uses the insert of Example Birch.", "Example Birch", "The clip insert in this example is felt."),
            ("Claim 3", "The straight clip of claim 1 uses the insert of Example Elm.", "Example Elm", "The clip insert in this example is cork.")],
        ["Claim 1. A folding bookmark comprising a clip and a replaceable insert.", "The bookmark cover can carry a cork label."]),
    family("spool", "selection", "en", [
        "For the travel yarn spool, how many grooves guide the cord?",
        "How many cord-guide grooves are specified on the travel spool?",
        "For the desktop yarn spool, how many grooves guide the cord?",
        "What yarn diameter does the travel spool accept?"],
        ["three", "five"], [
            ("Description 4", "The travel configuration uses the drum drawn in Plate F.", "Plate F", "Drum detail: three grooves guide the cord."),
            ("Description 5", "The desktop configuration uses the drum drawn in Plate J.", "Plate J", "Drum detail: five grooves guide the cord.")],
        ["The travel foot contains five decorative grooves.", "Cord may be unwound manually in either configuration."]),
    family("frame", "dev", "en", [
        "Which fastener is specified for the upright picture stand?",
        "For the picture stand in its upright form, identify the fastener.",
        "Which fastener is specified for the inclined picture stand?",
        "Which alloy is required for the picture stand fastener?"],
        ["wooden peg", "threaded pin"], [
            ("Paragraph 6", "The upright stand adopts the joint illustrated in Detail L.", "Detail L", "The illustrated joint is secured by a wooden peg."),
            ("Paragraph 8", "For the inclined stand, the joint illustrated in Detail R is used.", "Detail R", "The illustrated joint is secured by a threaded pin.")],
        ["An inclined edge can be ornamented with a wooden peg.", "The stand carries a picture on its front face."]),
    family("tray", "dev", "en", [
        "In the nesting tray of claim 4, what lining does the inherited rim require?",
        "Identify the required rim lining inherited by nesting-tray claim 4.",
        "In the nesting tray of claim 5, what lining does the inherited rim require?",
        "For the nesting tray of claim 4, what wall thickness is required?"],
        ["linen", "wool"], [
            ("Claim 4", "A nesting tray as in claim 1, further comprising a folding partition.", "Claim 1", "A tray comprising a rim having a linen lining."),
            ("Claim 5", "A nesting tray as in claim 3, further comprising a folding partition.", "Claim 3", "A tray comprising a rim having a wool lining.")],
        ["Description: the tray handle may have a wool covering.", "Example: a linen square may separate two stored trays."]),
    family("dial", "dev", "en", [
        "On the desk calendar, how is the dial indexed in the pocket embodiment?",
        "Identify the indexing mechanism for the desk calendar dial in its pocket embodiment.",
        "On the desk calendar, how is the dial indexed in the folding embodiment?",
        "What minimum indexing force does the desk calendar specify?"],
        ["spring tongue", "sliding tooth"], [
            ("Embodiment P", "The pocket embodiment incorporates the dial stop listed in Schedule Blue.", "Schedule Blue", "Dial index entry: a spring tongue engages the date ring."),
            ("Embodiment F", "The folding embodiment incorporates the dial stop listed in Schedule Green.", "Schedule Green", "Dial index entry: a sliding tooth engages the date ring.")],
        ["The folding cover can be closed by a spring tongue.", "A sliding tooth guides the pocket flap on withdrawal."]),
]
