# Frontend — AI Developer Assistant

React + Vite chat UI jo backend ke saare endpoints use karti hai.

## Setup

```bash
npm install
npm run dev
```

Khulta hai `http://localhost:5173` pe — ye port backend ke `CORS_ORIGINS` mein
pehle se allowed hai.

Backend kisi aur address pe ho toh `.env` bana lo:

```bash
cp .env.example .env    # phir VITE_API_URL badal do
```

## Commands

```bash
npm run dev       # dev server
npm run build     # production build (dist/)
npm run preview   # build ko locally serve karo
npm run lint      # oxlint
```

## Kya kya kaam karta hai

- **Streaming chat** — jawab token-by-token aata hai, blinking cursor ke saath
- **Stop button** — stream beech mein rok sakte ho; backend jitna jawab bana tha
  wo save kar leta hai
- **Conversation sidebar** — purani chats kholo ya delete karo
- **Validation** — khaali message aur 4000 se lamba message bhejne se pehle hi
  rok diya jaata hai (backend ki limit se match karta hai)
- **Health badge** — database reachable hai ya nahi

## Backend endpoints jo use hote hain

| Endpoint | Kahan |
|---|---|
| `POST /api/v1/chat` | message bhejna (streaming) |
| `GET /api/v1/chat/{id}` | purani chat kholna |
| `DELETE /api/v1/chat/{id}` | chat delete karna |
| `GET /api/v1/conversations` | sidebar ki list |
| `GET /health` | header ka status badge |

## Structure

```text
src/
├── api/client.js              # saare backend calls + streaming
├── components/
│   ├── ConversationList.jsx   # sidebar
│   ├── MessageList.jsx        # chat messages + auto-scroll
│   └── MessageInput.jsx       # textarea, counter, Send/Stop
├── App.jsx                    # state aur streaming logic
└── index.css                  # saari styling
```

## Dhyan dene wali baat

Backend `conversation_id` ko valid UUID hona zaruri karta hai. Agar database
mein purani conversations hain jinki id UUID nahi hai, wo sidebar mein dikhengi
aur khulengi bhi, par unme naya message bhejne par error aayega.
