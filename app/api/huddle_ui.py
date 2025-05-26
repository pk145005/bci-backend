from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/huddle", response_class=HTMLResponse)
async def huddle_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>BCI Daily Huddle</title></head>
<body>
  <h2>Daily Huddle Entry</h2>

  <label>Event type:</label>
  <select id="etype">
    <option value="huddle">Huddle</option>
    <option value="workout">Workout</option>
  </select><br/><br/>

  <label>Mobility done?</label>
  <select id="mob">
    <option value="">Select…</option>
    <option value="Yes">Yes</option>
    <option value="No">No</option>
  </select><br/><br/>

  <label>Sleep last night (hours):</label>
  <input id="sleep" type="number" step="0.1"><br/><br/>

  <button id="send">Submit</button>
  <pre id="status"></pre>

<script>
document.getElementById('send').onclick = async () => {
  const payload = {
    event_type: document.getElementById('etype').value,
    mobility:   document.getElementById('mob').value,
    sleep_hours: parseFloat(document.getElementById('sleep').value) || null
  };
  const res = await fetch('/event', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  document.getElementById('status').textContent =
    res.ok ? '✔ Saved!' : 'Error: '+await res.text();
};
</script>
</body>
</html>
""")
