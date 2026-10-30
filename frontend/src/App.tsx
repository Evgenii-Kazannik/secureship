import { useRef, useState } from "react";
import { useChatChatPost } from "./api/generated/secureship";

type Message = { role: "user" | "assistant"; text: string };

export default function App() {
  const sessionId = useRef(crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { mutate, isPending } = useChatChatPost({
    mutation: {
      onSuccess: (response) => {
        if (response.status === 200) {
          setMessages((m) => [...m, { role: "assistant", text: response.data.reply }]);
          setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 0);
        }
      },
    },
  });

  function send() {
    const text = input.trim();
    if (!text || isPending) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    mutate({ data: { session_id: sessionId.current, message: text } });
  }

  return (
    <div style={{ maxWidth: 640, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <h1 style={{ marginBottom: "1rem" }}>SecureShip</h1>
      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: 8,
          padding: 16,
          minHeight: 320,
          maxHeight: 480,
          overflowY: "auto",
          marginBottom: 8,
          background: "#fafafa",
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: "#999", margin: 0 }}>Ask about your shipment…</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{ textAlign: m.role === "user" ? "right" : "left", margin: "8px 0" }}
          >
            <span
              style={{
                background: m.role === "user" ? "#0070f3" : "#e9e9e9",
                color: m.role === "user" ? "#fff" : "#000",
                padding: "6px 12px",
                borderRadius: 16,
                display: "inline-block",
                maxWidth: "80%",
                wordBreak: "break-word",
              }}
            >
              {m.text}
            </span>
          </div>
        ))}
        {isPending && <div style={{ color: "#999", fontSize: 20 }}>…</div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: 8,
            border: "1px solid #ccc",
            fontSize: 15,
          }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type a message…"
          disabled={isPending}
          autoFocus
        />
        <button
          onClick={send}
          disabled={isPending || !input.trim()}
          style={{ padding: "8px 16px", borderRadius: 8, cursor: "pointer" }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
