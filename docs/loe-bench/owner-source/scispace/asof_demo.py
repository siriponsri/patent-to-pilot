"""Reproduce the as-of / survivor-bias demo from two Wayback-captured Orange Book zips (stdlib only)."""
import csv, datetime as dt
def load(p):
    rows=list(csv.DictReader(open(p,encoding='latin-1'),delimiter='~',quoting=csv.QUOTE_NONE))
    return rows
def d(s):
    try: return dt.datetime.strptime(s.strip(),'%b %d, %Y').date()
    except Exception: return None
a=load('ob_snap/s2019/patent.txt'); b=load('ob_snap/s2026/patent.txt')
cut=dt.date(2019,12,13)
key=lambda r:(r['Appl_No'],r['Product_No'],r['Patent_No'])
ka={key(r) for r in a}; kb={key(r) for r in b}
print('2019 rows',len(a),'with Submission_Date',sum(1 for r in a if r['Submission_Date'].strip()))
print('2026 rows',len(b),'with Submission_Date',sum(1 for r in b if r['Submission_Date'].strip()))
print('distinct keys 2019',len(ka),'absent in 2026',len(ka-kb),'new in 2026',len(kb-ka))
cand=[r for r in b if d(r['Submission_Date']) and d(r['Submission_Date'])<=cut and d(r['Patent_Expire_Date_Text']) and d(r['Patent_Expire_Date_Text'])>cut]
miss=[r for r in cand if key(r) not in ka]
print('2026 rows submitted<=cutoff & unexpired at cutoff',len(cand),'absent from 2019 snapshot',len(miss),round(100*len(miss)/len(cand),2),'%')
for r in miss[:3]: print(r['Appl_No'],r['Patent_No'],r['Submission_Date'])