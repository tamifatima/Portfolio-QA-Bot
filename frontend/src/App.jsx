/*
=============================================================
  App.jsx  —  React Frontend Chat Interface
=============================================================

PURPOSE:
  This is the entire frontend: a clean chat UI that:
    1. Sends user questions to FastAPI /chat endpoint
    2. Displays AI responses with animated streaming feel
    3. Shows source documents (which chunks the AI used)
    4. Has a "New Chat" button that resets conversation memory
    5. Auto-scrolls to the latest message

STATE MANAGEMENT:
  We use React's useState and useRef hooks — no Redux needed
  for a project this size.

  messages    → array of {role, content, sources} objects
  input       → the current value of the text input
  loading     → true while waiting for API response
  showSources → which message's sources are expanded

STYLING:
  Pure CSS-in-JS (style objects) — no Tailwind needed.
  Color palette: deep navy + electric indigo + soft white.
  Typography: Inter for body, monospace for source code blocks.
=============================================================
*/

import { useState, useRef, useEffect } from "react";

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:8000";  // FastAPI server URL

// Suggested starter questions shown before first message
const STARTER_QUESTIONS = [
  "What projects has Tahreem built?",
  "What are her technical skills?",
  "Tell me about her education",
  "What internships has she done?",
  "What is ShieldHer?",
];

// ─── STYLES ──────────────────────────────────────────────────────────────────
//
// Defined as JS objects so everything stays in one file.
// No CSS file needed for a project this size.
//
const styles = {
  // ── Layout ──
  app: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #0f0c29, #1a1a4e, #0f0c29)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    fontFamily: "'Inter', -apple-system, sans-serif",
    color: "#e8e8f0",
  },
  container: {
    width: "100%",
    maxWidth: "780px",
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    padding: "0 16px",
    boxSizing: "border-box",
  },

  // ── Header ──
  header: {
    padding: "20px 0 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid rgba(139,92,246,0.2)",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: "12px" },
  avatar: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    background: "linear-gradient(135deg, #6d28d9, #4f46e5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    fontWeight: "700",
    color: "white",
    flexShrink: 0,
  },
  headerTitle: { margin: 0, fontSize: "16px", fontWeight: "600", color: "#f0f0ff" },
  headerSub: { margin: "2px 0 0", fontSize: "12px", color: "#8b8bbd" },
  resetBtn: {
    padding: "7px 14px",
    background: "transparent",
    border: "1px solid rgba(139,92,246,0.4)",
    borderRadius: "8px",
    color: "#a78bfa",
    fontSize: "13px",
    cursor: "pointer",
    transition: "all 0.2s",
  },

  // ── Messages area ──
  messagesArea: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 0",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },

  // ── Empty / welcome state ──
  welcome: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    flex: 1,
    gap: "24px",
    padding: "40px 0",
  },
  welcomeIcon: { fontSize: "48px" },
  welcomeTitle: { margin: 0, fontSize: "22px", fontWeight: "700", color: "#f0f0ff" },
  welcomeSub: { margin: "6px 0 0", fontSize: "14px", color: "#8b8bbd", textAlign: "center" },
  starterGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "10px",
    width: "100%",
    maxWidth: "560px",
  },
  starterBtn: {
    padding: "12px 14px",
    background: "rgba(109,40,217,0.12)",
    border: "1px solid rgba(139,92,246,0.25)",
    borderRadius: "10px",
    color: "#c4b5fd",
    fontSize: "13px",
    cursor: "pointer",
    textAlign: "left",
    lineHeight: "1.4",
    transition: "all 0.2s",
  },

  // ── Message bubbles ──
  messageRow: (role) => ({
    display: "flex",
    justifyContent: role === "user" ? "flex-end" : "flex-start",
    alignItems: "flex-start",
    gap: "10px",
  }),
  botAvatar: {
    width: "30px",
    height: "30px",
    borderRadius: "50%",
    background: "linear-gradient(135deg, #6d28d9, #4f46e5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
    flexShrink: 0,
    marginTop: "2px",
  },
  bubble: (role) => ({
    maxWidth: "75%",
    padding: "12px 16px",
    borderRadius: role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    background: role === "user"
      ? "linear-gradient(135deg, #6d28d9, #4f46e5)"
      : "rgba(255,255,255,0.06)",
    border: role === "user" ? "none" : "1px solid rgba(255,255,255,0.08)",
    fontSize: "14px",
    lineHeight: "1.6",
    color: role === "user" ? "#fff" : "#e2e2f0",
    wordBreak: "break-word",
  }),

  // ── Sources accordion ──
  sourcesToggle: {
    marginTop: "8px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background: "transparent",
    border: "none",
    color: "#8b8bbd",
    fontSize: "12px",
    cursor: "pointer",
    padding: "0",
  },
  sourcesBox: {
    marginTop: "6px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  sourceChip: {
    background: "rgba(109,40,217,0.1)",
    border: "1px solid rgba(139,92,246,0.2)",
    borderRadius: "8px",
    padding: "8px 10px",
    fontSize: "12px",
    color: "#a78bfa",
    lineHeight: "1.5",
  },

  // ── Loading dots ──
  loadingBubble: {
    display: "flex",
    gap: "5px",
    padding: "14px 16px",
    background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "18px 18px 18px 4px",
    alignItems: "center",
  },
  dot: (delay) => ({
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    background: "#6d28d9",
    animation: "bounce 1.2s infinite",
    animationDelay: delay,
  }),

  // ── Input area ──
  inputArea: {
    padding: "12px 0 20px",
    borderTop: "1px solid rgba(139,92,246,0.2)",
  },
  inputRow: {
    display: "flex",
    gap: "10px",
    alignItems: "flex-end",
  },
  textarea: {
    flex: 1,
    padding: "12px 16px",
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(139,92,246,0.3)",
    borderRadius: "12px",
    color: "#f0f0ff",
    fontSize: "14px",
    resize: "none",
    outline: "none",
    lineHeight: "1.5",
    fontFamily: "inherit",
    minHeight: "48px",
    maxHeight: "120px",
  },
  sendBtn: (disabled) => ({
    padding: "12px 20px",
    background: disabled ? "rgba(109,40,217,0.3)" : "linear-gradient(135deg, #6d28d9, #4f46e5)",
    border: "none",
    borderRadius: "12px",
    color: "white",
    fontSize: "18px",
    cursor: disabled ? "not-allowed" : "pointer",
    transition: "opacity 0.2s",
    flexShrink: 0,
    height: "48px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  }),
};


// ─── MAIN COMPONENT ──────────────────────────────────────────────────────────
export default function App() {

  // ── State ──────────────────────────────────────────────────────────────────
  //
  // messages: array of { id, role, content, sources }
  //   role = "user" | "assistant" | "error"
  //   sources = array of { content, source } (from the API)
  //
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [openSourceId, setOpenSourceId] = useState(null); // which msg's sources are open

  // ── Refs ───────────────────────────────────────────────────────────────────
  //
  // messagesEndRef: a hidden div at the bottom of the message list.
  // We call scrollIntoView() on it to auto-scroll after each new message.
  //
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // ── Auto-scroll effect ─────────────────────────────────────────────────────
  //
  // useEffect runs after every render where `messages` or `loading` changed.
  // scrollIntoView({ behavior: "smooth" }) animates the scroll.
  //
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);


  // ── sendMessage ────────────────────────────────────────────────────────────
  //
  // The core function. Called when user clicks Send or presses Enter.
  //
  // Steps:
  //   1. Add user message to state immediately (optimistic UI)
  //   2. Clear input, set loading=true
  //   3. POST to /chat endpoint
  //   4. Add assistant response to state
  //   5. Handle errors
  //
  const sendMessage = async (questionText) => {
    const question = (questionText || input).trim();
    if (!question || loading) return;

    // Step 1: Add user message to the messages array immediately.
    // This makes the UI feel snappy — user sees their message right away.
    const userMsg = {
      id: Date.now(),
      role: "user",
      content: question,
      sources: [],
    };
    setMessages(prev => [...prev, userMsg]);

    // Step 2: Clear input and show loading state
    setInput("");
    setLoading(true);

    try {
      // Step 3: Call the FastAPI /chat endpoint
      //
      // fetch() is the browser's built-in HTTP client.
      // We send a POST request with a JSON body.
      //
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",  // tell server we're sending JSON
        },
        body: JSON.stringify({
          question: question,
          session_id: "default",
        }),
      });

      // If the server returned a non-2xx status code, throw an error
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Server error");
      }

      // Parse the JSON response body
      // response = { answer: "...", sources: [{content, source}, ...] }
      const data = await response.json();

      // Step 4: Add assistant message to state
      const assistantMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages(prev => [...prev, assistantMsg]);

    } catch (error) {
      // Step 5: On error, show an error message in the chat
      console.error("Chat error:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: "error",
        content: `⚠️ Error: ${error.message}. Is the backend running on port 8000?`,
        sources: [],
      }]);
    } finally {
      // Always reset loading state, whether success or error
      setLoading(false);
    }
  };


  // ── resetChat ──────────────────────────────────────────────────────────────
  //
  // Clears the UI messages AND tells the backend to clear its memory.
  //
  const resetChat = async () => {
    setMessages([]);
    setOpenSourceId(null);
    try {
      // POST /reset → clears ConversationBufferWindowMemory on the server
      await fetch(`${API_BASE}/reset`, { method: "POST" });
    } catch (e) {
      console.warn("Could not reset server memory:", e);
    }
  };


  // ── handleKeyDown ──────────────────────────────────────────────────────────
  //
  // Allow pressing Enter to send (but Shift+Enter for newline).
  //
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();  // prevent newline in textarea
      sendMessage();
    }
  };


  // ── JSX RENDER ─────────────────────────────────────────────────────────────
  return (
    <>
      {/* Bounce animation for loading dots */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-8px); }
        }
        * { box-sizing: border-box; }
        body { margin: 0; }
        textarea::placeholder { color: #6b6b9a; }
        textarea:focus { border-color: rgba(139,92,246,0.6) !important; }
        button:hover { opacity: 0.85; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 2px; }
      `}</style>

      <div style={styles.app}>
        <div style={styles.container}>

          {/* ── HEADER ── */}
          <header style={styles.header}>
            <div style={styles.headerLeft}>
              <div style={styles.avatar}>T</div>
              <div>
                <p style={styles.headerTitle}>Tahreem's Portfolio Bot</p>
                <p style={styles.headerSub}>Powered by RAG + GPT-4o-mini</p>
              </div>
            </div>
            {messages.length > 0 && (
              <button style={styles.resetBtn} onClick={resetChat}>
                + New Chat
              </button>
            )}
          </header>

          {/* ── MESSAGES AREA ── */}
          <div style={styles.messagesArea}>

            {/* Welcome / empty state — shown before any messages */}
            {messages.length === 0 && !loading && (
              <div style={styles.welcome}>
                <div style={styles.welcomeIcon}>👩‍💻</div>
                <div style={{ textAlign: "center" }}>
                  <p style={styles.welcomeTitle}>Ask me anything about Tahreem</p>
                  <p style={styles.welcomeSub}>
                    Projects, skills, education, experience — I know it all!
                  </p>
                </div>

                {/* Starter question chips */}
                <div style={styles.starterGrid}>
                  {STARTER_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      style={styles.starterBtn}
                      onClick={() => sendMessage(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Render each message */}
            {messages.map((msg) => (
              <div key={msg.id} style={styles.messageRow(msg.role)}>

                {/* Bot avatar — only shown for assistant messages */}
                {msg.role === "assistant" && (
                  <div style={styles.botAvatar}>✨</div>
                )}

                <div style={{ maxWidth: "75%" }}>
                  {/* The message bubble */}
                  <div style={styles.bubble(msg.role === "error" ? "assistant" : msg.role)}>
                    {msg.content}
                  </div>

                  {/* Sources accordion — only for assistant messages with sources */}
                  {msg.role === "assistant" && msg.sources.length > 0 && (
                    <div>
                      {/* Toggle button */}
                      <button
                        style={styles.sourcesToggle}
                        onClick={() => setOpenSourceId(
                          openSourceId === msg.id ? null : msg.id
                        )}
                      >
                        <span>{openSourceId === msg.id ? "▾" : "▸"}</span>
                        <span>
                          {msg.sources.length} source{msg.sources.length > 1 ? "s" : ""} used
                        </span>
                      </button>

                      {/* Source chunks — shown when toggle is open */}
                      {openSourceId === msg.id && (
                        <div style={styles.sourcesBox}>
                          {msg.sources.map((src, i) => (
                            <div key={i} style={styles.sourceChip}>
                              <strong style={{ fontSize: "11px", opacity: 0.7 }}>
                                📄 {src.source.split("/").pop()}
                              </strong>
                              <br />
                              {src.content.slice(0, 200)}
                              {src.content.length > 200 ? "..." : ""}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator — shown while waiting for API response */}
            {loading && (
              <div style={styles.messageRow("assistant")}>
                <div style={styles.botAvatar}>✨</div>
                <div style={styles.loadingBubble}>
                  {/* Three bouncing dots with staggered animation delays */}
                  <div style={styles.dot("0s")} />
                  <div style={styles.dot("0.2s")} />
                  <div style={styles.dot("0.4s")} />
                </div>
              </div>
            )}

            {/* Invisible div at the bottom — scrolled into view after each message */}
            <div ref={messagesEndRef} />
          </div>

          {/* ── INPUT AREA ── */}
          <div style={styles.inputArea}>
            <div style={styles.inputRow}>
              <textarea
                ref={textareaRef}
                style={styles.textarea}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about projects, skills, education..."
                rows={1}
                disabled={loading}
              />
              <button
                style={styles.sendBtn(loading || !input.trim())}
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                aria-label="Send message"
              >
                ➤
              </button>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
