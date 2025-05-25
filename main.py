from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import date
from fastapi.responses import HTMLResponse
import logging
import gspread
import json
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BCI Core")
from app.api import summary as summary_api
app.include_router(summary_api.router)

# Test-error endpoint
default_error = "TEST_ERROR_ALERT"
@app.get("/test-error", status_code=500)
async def test_error():
    logging.error(default_error)
    return {"detail": "Error logged"}

# Google Sheets setup
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]
creds = Credentials.from_service_account_file("gspread-key.json", scopes=SCOPES)
gc = gspread.authorize(creds)

# Open the DUMI spreadsheet and worksheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZYlDf8xfgIxnDgUOr3HEqxM3b4VlA42GNU-403clyw/edit"
sh = gc.open_by_url(SHEET_URL)
body_ws = sh.worksheet("Body")
workouts_ws = sh.worksheet("Workouts")

# Shared upsert helper
def upsert_row(ws, data: dict):
    """Update existing row by Date or insert new row at index 2."""
    headers = ws.row_values(1)
    idx_map = {h: i for i, h in enumerate(headers)}
    row = [''] * len(headers)
    for key, val in data.items():
        if key in idx_map and val is not None:
            row[idx_map[key]] = str(val)
    dates = ws.col_values(1)
    date_val = data.get("Date")
    end_col = chr(ord('A') + len(headers) - 1)
    if date_val in dates:
        idx = dates.index(date_val) + 1
        ws.update(f"A{idx}:{end_col}{idx}", [row])
        logging.info(f"Updated row {idx} in {ws.title}: {data}")
    else:
        ws.insert_row(row, index=2)
        logging.info(f"Inserted new row in {ws.title}: {data}")

# Pydantic model for daily metrics
class DailyMetric(BaseModel):
    date: date
    bodyweight: float
    sleep: float

@app.post("/record")
async def record_daily(metric: DailyMetric):
    """Upsert daily metrics into Body sheet."""
    data = {
        "Date": metric.date.isoformat(),
        "Bodyweight": metric.bodyweight,
        "Sleep": metric.sleep
    }
    upsert_row(body_ws, data)
    return {"status": "ok"}

# Workout split definitions (Machine Row replaces Bent-Over Rows, RDL first)
SPLITS = {
    "push": ["DB Bench", "Overhead Press", "Rope Push-Downs", "Lateral Raise", "Woodchoppers"],
    "pull": ["RDL", "Lat Pulldowns", "Machine Row", "Face Pulls", "Hanging Leg Raises"],
    "legs": ["Squat", "Lunges", "Leg Extensions", "Leg Curls", "Adductor", "Machine Crunches"]
}

@app.post("/record-workout")
async def record_workout(data: dict):
    """Upsert workout data into Workouts sheet or skip if no workout."""
    if data.get("worked_out") != "yes":
        logging.info(f"No workout to record for date {data.get('date')}")
        return {"status": "no_data"}
    row_data = {
        "Date": data.get("date"),
        "Mobility": data.get("mobility"),
        "Split": data.get("split")
    }
    for ex in SPLITS.get(data.get("split", ""), []):
        key = ex.lower().replace(' ', '_').replace('-', '_')
        for suffix, hdr in [("kg", f"{ex} (kg)"), ("sets", f"{ex} Sets"), ("reps", f"{ex} Reps")]:
            val = data.get(f"{key}_{suffix}")
            if val is not None:
                row_data[hdr] = val
    upsert_row(workouts_ws, row_data)
    return {"status": "ok"}

@app.get("/huddle", response_class=HTMLResponse)
def huddle_page():
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>BCI Daily Huddle</title></head>
<body>
  <h1>BCI Daily Huddle</h1>
  <form id="huddleForm">
    <label>Bodyweight (kg)?</label><br/><input name="bodyweight" type="number" step="0.1"/><br/><br/>
    <label>Sleep (hrs)?</label><br/><input name="sleep" type="number" step="0.1"/><br/><br/>
  </form>
  <button id="submitBtn">Submit</button>
  <pre id="status"></pre>
  <script>
    document.getElementById('submitBtn').onclick = async () => {
      const f = new FormData(document.getElementById('huddleForm'));
      const p = { date: new Date().toISOString().slice(0,10),
        bodyweight: parseFloat(f.get('bodyweight')), sleep: parseFloat(f.get('sleep')) };
      const r = await fetch('/record',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
      const s = document.getElementById('status');
      if(!r.ok) s.textContent = `Error: ${await r.text()}`;
      else { s.textContent='Saved! Redirecting...'; setTimeout(()=>location.href='/huddle-workout',500); }
    };
  </script>
</body>
</html>""")

@app.get("/huddle-workout", response_class=HTMLResponse)
def huddle_workout_page():
    js = json.dumps(SPLITS)
    html = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>BCI Workout Entry</title></head>
<body>
  <h1>BCI Workout Entry</h1>
  <form id="workoutForm">
    <div id="step-1">
      <label>Workout today?</label><br/>
      <select id="workedOut"><option value="">Select...</option><option value="yes">Yes</option><option value="no">No</option></select>
    </div>
    <div id="step-2" style="display:none;">
      <label>Which split?</label><br/>
      <select id="splitSelect"><option value="">Select...</option></select>
    </div>
    <div id="step-3" style="display:none;"><div id="exerciseFields"></div></div>
  </form>
  <button id="submitWorkout">Submit Workout</button>
  <pre id="statusWorkout"></pre>
<script>
const SPLITS = %s;
document.getElementById('workedOut').onchange = e => {
  const s2 = document.getElementById('step-2'); const sc = document.getElementById('splitSelect');
  if(e.target.value==='yes'){
    s2.style.display='block'; sc.innerHTML='<option value="">Select...</option>';
   (Object.keys(SPLITS).forEach(s=>sc.appendChild(new Option(s.charAt(0).toUpperCase()+s.slice(1),s)));
  } else { document.getElementById('step-3').style.display='none'; s2.style.display='none'; }
};
document.getElementById('splitSelect').onchange = e => {
  const f = document.getElementById('exerciseFields');
  f.innerHTML = '<label>Mobility done?</label><br/><select name="mobility"><option value="">Select...</option><option value="Yes">Yes</option><option value="No">No</option></select><br/><br/>';
  SPLITS[e.target.value].forEach(ex=>{
    const id = ex.toLowerCase().replace(/[^a-z]/g,'_');
    ['kg','sets','reps'].forEach(suf=>f.innerHTML += `<label>${ex} ${suf.toUpperCase()}</label><br/><input name="${id}_${suf}" type="number"/><br/>`);
    f.innerHTML += '<br/>';
  });
  document.getElementById('step-3').style.display='block';
};
document.getElementById('submitWorkout').onclick = async () => {
  const data = { date:new Date().toISOString().slice(0,10), worked_out:document.getElementById('workedOut').value, split:document.getElementById('splitSelect').value };
  new FormData(document.getElementById('workoutForm')).forEach((v,k)=>data[k]=parseFloat(v)||v);
  const res = await fetch('/record-workout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  document.getElementById('statusWorkout').textContent = res.ok?'Workout recorded!':'Error: '+await res.text();
};
</script>
</body>
</html>""" % js
    return HTMLResponse(content=html)
