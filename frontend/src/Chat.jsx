// import React, { useState } from "react";

// const API_BASE = "http://localhost:8000/api/v1";

// export default function Chat() {
//   const [messages, setMessages] = useState([]);
//   const [input, setInput] = useState("");

//   // ---------------------------------------------------------------------------
//   // SEND STREAM MESSAGE (JSON-RPC)
//   // ---------------------------------------------------------------------------
//   async function sendMessage() {
//     const payload = {
//       id: crypto.randomUUID(),
//       jsonrpc: "2.0",
//       method: "message/stream",
//       params: {
//         message: {
//           kind: "message",
//           messageId: crypto.randomUUID(),
//           role: "user",

//           // required in Solace Agent Mesh
//           metadata: {
//             agent_name: "ManufacturingOrchestrator",
//           },

//           parts: [
//             {
//               kind: "text",
//               text: input,
//             },
//           ],
//         },
//       },
//     };

//     console.log("Sending streaming message:", payload);

//     const res = await fetch(`${API_BASE}/message:stream`, {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify(payload),
//       credentials: "include",
//     });

//     const data = await res.json();
//     console.log("Response:", data);

//     const taskId =
//       data?.result?.id || data?.id || null;

//     if (!taskId) {
//       console.error("No taskId returned!", data);
//       return;
//     }

//     console.log("TASK ID:", taskId);
//     subscribeSSE(taskId);
//   }

//   // ---------------------------------------------------------------------------
//   // SUBSCRIBE TO SSE STREAM
//   // ---------------------------------------------------------------------------
//   function subscribeSSE(taskId) {
//     const url = `${API_BASE}/sse/subscribe/${taskId}`;
//     console.log("Connecting SSE:", url);

//     const es = new EventSource(url, { withCredentials: true });

//     es.onmessage = (event) => {
//       console.log("SSE EVENT:", event.data);

//       try {
//         setMessages((prev) => [...prev, JSON.parse(event.data)]);
//       } catch {
//         setMessages((prev) => [...prev, event.data]);
//       }
//     };

//     es.onerror = (err) => {
//       console.error("SSE error:", err);
//       es.close(); // SAM closes stream when task is done
//     };
//   }

//   // ---------------------------------------------------------------------------
//   // UI
//   // ---------------------------------------------------------------------------
//   return (
//     <div style={{ padding: 20 }}>
//       <h2>SAM Gateway Chat</h2>

//       <textarea
//         rows="3"
//         value={input}
//         style={{ width: "300px" }}
//         onChange={(e) => setInput(e.target.value)}
//       />

//       <br />
//       <button onClick={sendMessage}>Send</button>

//       <h3>Messages:</h3>
//       <pre>{JSON.stringify(messages, null, 2)}</pre>
//     </div>
//   );
// }

// import React, { useState } from "react";

// const API_BASE = "http://localhost:9000/api/v2";
// const AUTH_TOKEN = "token"; // change if needed

// export default function Chat() {
//   const [messages, setMessages] = useState([]);
//   const [input, setInput] = useState("");
//   const [loading, setLoading] = useState(false);

//   async function sendMessage() {
//     setLoading(true);

//     // FormData because API requires multipart/form-data
//     const form = new FormData();
//     form.append("agent_name", "ManufacturingOrchestrator");
//     form.append("prompt", input);

//     console.log("Submitting task:", input);

//     // --- SUBMIT TASK ---
//     const res = await fetch(`${API_BASE}/tasks`, {
//       method: "POST",
//       headers: {
//         Authorization: `Bearer ${AUTH_TOKEN}`,
//       },
//       body: form
//     });

//     if (!res.ok) {
//       console.error("Task submit failed:", await res.text());
//       setLoading(false);
//       return;
//     }

//     const data = await res.json();
//     console.log("Task submitted:", data);

//     const taskId = data.taskId;
//     if (!taskId) {
//       console.error("No taskId returned");
//       setLoading(false);
//       return;
//     }

//     // Start polling
//     pollTask(taskId);
//   }

//   // --- POLLING FUNCTION ---
// async function pollTask(taskId) {
//   console.log("Polling:", taskId);

//   const interval = setInterval(async () => {
//     const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
//       headers: {
//         Authorization: `Bearer ${AUTH_TOKEN}`,
//       }
//     });

//     let text = await res.text();

//     if (!text || text.trim().length === 0) {
//       console.warn("Empty response from gateway, skipping...");
//       return; // continue polling without breaking
//     }

//     let data;
//     try {
//       data = JSON.parse(text);
//     } catch (err) {
//       console.error("Malformed JSON:", text);
//       return;
//     }

//     console.log("Poll:", data);

//     if (data?.status?.state === "completed") {
//       clearInterval(interval);
//       setMessages((prev) => [...prev, data.status.message]);
//       setLoading(false);
//     }
//   }, 1500);
// }


//   return (
//     <div style={{ padding: 20 }}>
//       <h2>REST Gateway Chat (Polling)</h2>

//       <textarea
//         rows={3}
//         placeholder="Type your message..."
//         value={input}
//         onChange={(e) => setInput(e.target.value)}
//         style={{ width: "300px" }}
//       />

//       <br />
//       <button onClick={sendMessage} disabled={loading}>
//         {loading ? "Processing..." : "Send"}
//       </button>

//       <h3>Messages:</h3>
//       <pre style={{ background: "#eee", padding: 10 }}>
//         {JSON.stringify(messages, null, 2)}
//       </pre>
//     </div>
//   );
// }
import React, { useState } from "react";

const API_BASE = "http://localhost:9000/api/v2";
const AUTH_TOKEN = "token";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // -----------------------------
  // Send Message
  // -----------------------------
  async function sendMessage() {
    if (!input.trim()) return;

    setLoading(true);

    const form = new FormData();
    form.append("agent_name", "ManufacturingOrchestrator");
    form.append("prompt", input);

    console.log("Submitting task:", input);

    const res = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
      },
      body: form,
    });

    if (!res.ok) {
      console.error("Task submit failed:", await res.text());
      setLoading(false);
      return;
    }

    const data = await res.json();
    console.log("Task submitted:", data);

    // FIX: support multiple taskId styles
    const taskId = data.taskId || data.id || data["task_id"];

    if (!taskId) {
      console.error("No taskId returned:", data);
      setLoading(false);
      return;
    }

    pollTask(taskId);
  }

  // -----------------------------
  // Poll Task
  // -----------------------------
  function pollTask(taskId) {
    console.log("Polling:", taskId);

    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${AUTH_TOKEN}`,
        },
      });

      const text = await res.text();

      if (!text || text.trim().length === 0) {
        console.warn("Empty response, continuing...");
        return;
      }

      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        console.error("Invalid JSON:", text);
        return;
      }

      console.log("Poll:", data);

      if (data?.status?.state === "completed") {
        clearInterval(interval);

        const reply = data.status.message?.parts?.[0]?.text || "No reply";
        setMessages((prev) => [...prev, { role: "agent", text: reply }]);

        setLoading(false);
      }
    }, 1500);
  }

  // -----------------------------
  // JSX UI
  // -----------------------------
  return (
    <div className="min-h-screen bg-gray-900 p-6 text-white flex flex-col items-center">
      <div className="w-full max-w-3xl">

        <h1 className="text-3xl font-bold mb-6 text-center">
          REST Gateway Chat (Polling)
        </h1>

        {/* Chat Box */}
        <div className="bg-gray-800 rounded-xl p-4 shadow-lg mb-4 h-[500px] overflow-y-auto">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`mb-4 p-3 rounded-lg max-w-[80%] text-sm whitespace-pre-wrap ${
                m.role === "agent"
                  ? "bg-blue-600 text-white self-start"
                  : "bg-gray-700 text-gray-200 self-end"
              }`}
            >
              {m.text}
            </div>
          ))}
        </div>

        {/* Input Box */}
        <div className="flex gap-3">
          <textarea
            className="flex-1 p-3 bg-gray-800 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            placeholder="Type your message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <button
            onClick={sendMessage}
            disabled={loading}
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              loading
                ? "bg-gray-600 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {loading ? "Processing…" : "Send"}
          </button>
        </div>

      </div>
    </div>
  );
}
