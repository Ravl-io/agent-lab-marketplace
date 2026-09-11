#!/usr/bin/env python3
"""Build workspace/data/db/support.db. Facilitator tool — not shipped to participants."""
import os, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "workspace", "data", "db", "support.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)
if os.path.exists(DB):
    os.remove(DB)
c = sqlite3.connect(DB)

c.executescript("""
CREATE TABLE accounts (
  account_id TEXT PRIMARY KEY, name TEXT NOT NULL, plan TEXT NOT NULL,
  region TEXT NOT NULL, platform_version TEXT NOT NULL, sso_enabled INTEGER NOT NULL,
  seats INTEGER NOT NULL, created_at TEXT NOT NULL);

CREATE TABLE sso_domains (
  account_id TEXT NOT NULL, domain TEXT NOT NULL, added_at TEXT NOT NULL,
  PRIMARY KEY (account_id, domain));

CREATE TABLE users (
  user_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, email TEXT NOT NULL,
  name TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);

-- effective_to IS NULL means "still in force". An entitlement answer is only
-- correct as of a date, which is why this table is not a simple matrix.
CREATE TABLE entitlements (
  plan TEXT NOT NULL, feature TEXT NOT NULL, enabled INTEGER NOT NULL,
  effective_from TEXT NOT NULL, effective_to TEXT);

CREATE TABLE audit_log (
  event_id INTEGER PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT,
  action TEXT NOT NULL, target TEXT, result TEXT NOT NULL, error_code TEXT,
  detail TEXT, created_at TEXT NOT NULL);

CREATE TABLE vendor_cases (
  vendor_case_id TEXT PRIMARY KEY, known_issue TEXT, title TEXT NOT NULL,
  status TEXT NOT NULL, severity TEXT NOT NULL, opened_at TEXT NOT NULL,
  resolved_at TEXT, fix_version TEXT);

CREATE TABLE case_history (
  case_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, subject TEXT NOT NULL,
  classification TEXT, resolution TEXT, vendor_case TEXT,
  opened_at TEXT NOT NULL, closed_at TEXT);
""")

accounts = [
 ("acc-1042","Brightmoor Health","Enterprise","eu-west","5.4.1",1,480,"2025-02-11"),
 ("acc-2287","Kestrel Retail Group","Growth","us-east","5.4.1",1,95,"2024-09-03"),
 ("acc-3310","Aldermoor Logistics","Enterprise","eu-west","5.4.1",1,220,"2024-04-18"),
 ("acc-4188","Thornbury Media","Starter","us-east","5.4.1",0,12,"2026-01-22"),
 ("acc-5501","Calderwood Freight","Enterprise","eu-west","5.4.1",1,310,"2025-06-30"),
 ("acc-6620","Marlowe Financial","Enterprise","eu-west","5.4.0",1,640,"2023-11-14"),
 ("acc-7734","Pinehurst Clinics","Growth","us-east","5.4.1",1,58,"2025-10-02"),
 ("acc-8890","Vance & Ruel","Enterprise","ap-south","5.4.1",1,140,"2025-08-19"),
]
c.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", accounts)

c.executemany("INSERT INTO sso_domains VALUES (?,?,?)", [
 ("acc-1042","brightmoorhealth.com","2026-08-04"),   # the .org domain was never added
 ("acc-2287","kestrelretail.com","2025-01-15"),
 ("acc-3310","aldermoor.co.uk","2024-05-02"),
 ("acc-5501","calderwoodfreight.com","2025-07-11"),
 ("acc-6620","marlowefinancial.com","2024-01-08"),
 ("acc-6620","marlowe-fs.com","2025-03-19"),
 ("acc-7734","pinehurstclinics.com","2025-11-01"),
 ("acc-8890","vanceruel.com","2025-09-01"),
])

users = [
 ("usr-10","acc-1042","y.adeyemi@brightmoorhealth.com","Yusuf Adeyemi","Admin","active","2025-02-11"),
 ("usr-11","acc-1042","k.oduya@brightmoor-health.org","Kwame Oduya","Member","active","2026-08-28"),
 ("usr-12","acc-1042","t.finch@brightmoor-health.org","Tania Finch","Member","active","2026-08-28"),
 ("usr-13","acc-1042","a.silva@brightmoor-health.org","Ana Silva","Member","active","2026-08-29"),
 ("usr-14","acc-1042","r.brand@brightmoorhealth.com","Rob Brand","Member","active","2025-03-04"),
 ("usr-20","acc-2287","d.marsh@kestrelretail.com","Danielle Marsh","Admin","active","2024-09-03"),
 ("usr-21","acc-2287","j.okafor@kestrelretail.com","Joy Okafor","Member","active","2025-02-17"),
 ("usr-30","acc-3310","p.nowak@aldermoor.co.uk","Peter Nowak","Admin","active","2024-04-18"),
 ("usr-31","acc-3310","l.hume@aldermoor.co.uk","Liz Hume","Member","active","2024-06-01"),
 ("usr-40","acc-4188","unknown@thornburymedia.com","Unknown","Member","active","2026-01-22"),
 ("usr-50","acc-5501","s.mbeki@calderwoodfreight.com","Sipho Mbeki","Admin","active","2025-06-30"),
 ("usr-60","acc-6620","h.tanaka@marlowefinancial.com","Hana Tanaka","Admin","active","2023-11-14"),
]
c.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?)", users)

FEATURES = ["standard_reports","scheduled_reports","bulk_export","api_access",
            "saved_filters","sso","multi_sso_domain","sandbox_tenant"]
MATRIX = {  # current state
 "Starter":    {"standard_reports":1,"saved_filters":1},
 "Growth":     {"standard_reports":1,"scheduled_reports":1,"api_access":1,"saved_filters":1,"sso":1},
 "Enterprise": {f:1 for f in FEATURES},
}
ent = []
for plan in ("Starter","Growth","Enterprise"):
    for f in FEATURES:
        ent.append((plan, f, MATRIX[plan].get(f, 0), "2024-01-01", None))
# bulk_export moved Growth -> Enterprise on 2026-06-01: the historical row is kept,
# closed off, rather than overwritten. This is why "it worked in the spring" is true.
ent = [e for e in ent if not (e[0] == "Growth" and e[1] == "bulk_export")]
ent += [("Growth","bulk_export",1,"2024-01-01","2026-06-01"),
        ("Growth","bulk_export",0,"2026-06-01",None)]
c.executemany("INSERT INTO entitlements VALUES (?,?,?,?,?)", ent)

audit = []
n = [1]
def ev(acc, usr, action, target, result, code, detail, at):
    audit.append((n[0], acc, usr, action, target, result, code, detail, at)); n[0] += 1

# CASE-4471 — SSO domain never registered. Admin's own domain works; the .org users fall back.
for day in ("2026-08-31","2026-09-01","2026-09-02"):
    for usr, dom in (("usr-11","brightmoor-health.org"),("usr-12","brightmoor-health.org"),
                     ("usr-13","brightmoor-health.org")):
        ev("acc-1042", usr, "sso_login", dom, "denied", "DOMAIN_NOT_REGISTERED",
           "fell back to password login", f"{day} 08:1{audit.__len__()%6}:00")
ev("acc-1042","usr-10","sso_login","brightmoorhealth.com","success",None,
   "redirected to idp","2026-09-02 09:02:00")
ev("acc-1042","usr-14","sso_login","brightmoorhealth.com","success",None,
   "redirected to idp","2026-09-02 09:40:00")

# CASE-4482 — bulk export denied now, succeeded in the spring before the plan change.
ev("acc-2287","usr-20","bulk_export","orders 2026-08-01..2026-08-31","success",None,
   "1.2M rows","2026-04-14 11:03:00")
ev("acc-2287","usr-20","bulk_export","orders 2026-03-01..2026-03-31","success",None,
   "980k rows","2026-04-02 09:22:00")
for t in ("2026-09-04 14:24:00","2026-09-04 14:26:00","2026-09-04 15:01:00"):
    ev("acc-2287","usr-20","bulk_export","orders 2026-08-01..2026-08-31","denied",
       "NOT_ENTITLED","feature not in plan Growth", t)
ev("acc-2287","usr-21","bulk_export","orders 2026-08-01..2026-08-31","denied",
   "NOT_ENTITLED","feature not in plan Growth","2026-09-04 15:12:00")

# CASE-4495 — saves succeed, then the filters are gone the next morning. No error anywhere.
for day, nxt in (("2026-09-02","2026-09-03"),("2026-09-03","2026-09-04"),("2026-09-04","2026-09-05")):
    ev("acc-3310","usr-30","filter_save","dispatch-north","success",None,
       "filter persisted, id assigned", f"{day} 16:40:00")
    ev("acc-3310","usr-31","filter_save","dispatch-south","success",None,
       "filter persisted, id assigned", f"{day} 16:52:00")
    ev("acc-3310","usr-30","filter_list","-","success",None,
       "0 filters returned", f"{nxt} 07:05:00")
# another eu-west Enterprise account on 5.4.1 with the same signature
ev("acc-5501","usr-50","filter_save","depot-rota","success",None,"filter persisted","2026-09-03 17:10:00")
ev("acc-5501","usr-50","filter_list","-","success",None,"0 filters returned","2026-09-04 08:02:00")

ev("acc-4188","usr-40","report_view","weekly-summary","success",None,None,"2026-09-06 16:30:00")
c.executemany("INSERT INTO audit_log VALUES (?,?,?,?,?,?,?,?,?)", audit)

c.executemany("INSERT INTO vendor_cases VALUES (?,?,?,?,?,?,?,?)", [
 ("VND-411","KI-77","Saved filters not persisted for eu-west tenants","resolved","S2",
  "2026-07-21","2026-08-14","5.4.1"),
 ("VND-427","KI-81","Scheduled report emails delayed","open","S3","2026-08-19",None,None),
 ("VND-433","KI-84","Audit log UI search truncates at 1000 rows","open","S3","2026-08-29",None,"5.4.3"),
 ("VND-388","KI-62","SSO redirect loop on Safari 17","closed","S2","2026-04-30","2026-05-20","5.3.4"),
 ("VND-402","KI-70","Duplicate rows in order export","closed","S2","2026-06-10","2026-07-02","5.4.0"),
])

c.executemany("INSERT INTO case_history VALUES (?,?,?,?,?,?,?,?)", [
 ("CASE-4123","acc-3310","Saved filters disappear overnight","product_defect",
  "Escalated to vendor, fixed in 5.4.1","VND-411","2026-07-18","2026-08-15"),
 ("CASE-4180","acc-5501","Filters not saving","product_defect",
  "Linked to VND-411","VND-411","2026-07-25","2026-08-15"),
 ("CASE-4201","acc-2287","Cannot schedule report over 200k rows","product_defect",
  "Linked to VND-427","VND-427","2026-08-20",None),
 ("CASE-4233","acc-7734","SSO not working for new staff","configuration",
  "Second domain added to account","","2026-08-02","2026-08-02"),
 ("CASE-4256","acc-6620","Export missing columns","user_error",
  "Customer was using the standard report, not the export","","2026-08-06","2026-08-07"),
 ("CASE-4288","acc-2287","Bulk export button greyed out","user_error",
  "Bulk export moved to Enterprise 2026-06-01; scheduled report offered","","2026-08-11","2026-08-12"),
 ("CASE-4301","acc-8890","API returns 403 for all calls","configuration",
  "API key had been revoked by the customer's own admin","","2026-08-14","2026-08-14"),
 ("CASE-4344","acc-1042","Users prompted for password","configuration",
  "Second domain brightmoor-clinics.uk registered","","2026-08-20","2026-08-21"),
 ("CASE-4390","acc-6620","Audit log search shows fewer rows than expected","product_defect",
  "Linked to VND-433","VND-433","2026-08-28",None),
 ("CASE-4412","acc-7734","Report numbers differ from spreadsheet","user_error",
  "Different date range in the customer's spreadsheet","","2026-08-30","2026-09-01"),
])

c.commit()
counts = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in
          ("accounts","sso_domains","users","entitlements","audit_log","vendor_cases","case_history")}
c.close()
print("built", DB)
for t, k in counts.items():
    print(f"  {t:<16} {k}")
