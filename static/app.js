const chat = document.getElementById("chat");
const eventsBox = document.getElementById("events");
const form = document.getElementById("form");
const text = document.getElementById("text");

function addMsg(who, msg) {
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.textContent = msg;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function renderEvents(events) {
  eventsBox.innerHTML = "";
  for (const ev of events) {
    const div = document.createElement("div");
    div.className = "event";
    div.textContent = `${ev.ts}  [${ev.kind}]  ${ev.message || ""}`;
    eventsBox.appendChild(div);
  }
}

async function refreshEvents() {
  try {
    const r = await fetch("/api/events?limit=40");
    const data = await r.json();
    renderEvents(data.events || []);
  } catch (e) {
    // ignore
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const v = text.value.trim();
  if (!v) return;
  addMsg("user", v);
  text.value = "";

  try {
    const r = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: v }),
    });

    const data = await r.json();
    if (data.response) {
      addMsg("assistant", data.response);
    } else {
      addMsg("assistant", "(ok)");
    }
    if (data.events) renderEvents(data.events);
  } catch (err) {
    addMsg("assistant", "Error enviando mensaje: " + err);
  }
});

setInterval(refreshEvents, 3000);
refreshEvents();
