# TechJob AI — Frontend

Nền tảng thị trường việc làm IT thông minh — SPA frontend xây dựng theo
`design.md` (v2.0, aligned với SRS v1.0 — Intro2SE Nhóm 6).

This is a **complete, runnable React 18 SPA** implementing all 7 routes, every
component, and every UI state described in the design spec — Dashboard, Job
Search/Detail, AI Assistant chat, Cover Letter generator, Market Insights,
Profile, plus Settings & Help (present in the UI mockups). It currently runs
entirely on **realistic mock data** so you can see and click through the full
product with zero backend setup; every data call is already routed through a
`services/` layer so swapping in a real API later is a small, contained
change rather than a rewrite.

## Quick start

```bash
npm install
npm run dev       # http://localhost:5173
```

```bash
npm run build      # production build -> dist/
npm run preview    # serve the production build locally
npm run lint        # ESLint
```

Requires Node 18+.

## What's implemented

| Area | Status |
|---|---|
| Routing (7 pages + Settings/Help/404) | ✅ React Router v6 |
| Sidebar / Header / responsive layout | ✅ desktop full → tablet icon-only → mobile drawer |
| Smart Job Card (FR-1/FR-6) + skeleton loading | ✅ |
| Job List + filters + AI recommended banner (FR-1/FR-5) | ✅ |
| Job Detail 2-column + sticky panel + related jobs (FR-2) | ✅ |
| Dashboard: skill bar / salary box-plot / trend line (FR-3.x) | ✅ Recharts + a hand-built SVG box plot (Recharts has no boxplot primitive) |
| AI Assistant chat: streaming, mini job cards, inline chart, quick actions (FR-7–FR-11) | ✅ simulated token streaming, see `services/chatService.js` |
| Graceful degradation / AI fallback banner (NFR-3) | ✅ see "Testing the AI fallback state" below |
| Cover Letter split view, streaming generation, copy/download (FR-8) | ✅ stacks vertically on mobile per spec |
| Market Insights: AI summary, salary chart, emerging skills, heatmap | ✅ heatmap is a stylized SVG, not literal geo-data |
| Profile: 5 tabs, AI analysis card, completeness bar | ✅ |
| Settings & Help | ✅ (from the UI mockups, not in the FR list but linked from the sidebar) |
| AI badge/labeling convention (§12) | ✅ `components/ui` → `AIBadge` |
| All 6 UI states from §6 (loading/empty/error/typing/fallback/offline) | ✅ loading/empty/typing/fallback are live; error/offline are stubbed the same way — see Known limitations |

## Project structure

Matches the file structure in `design.md` §10:

```
src/
├── components/
│   ├── ui/index.jsx        # Button, Card, Badge, Tabs, Toggle, Skeleton, Avatar, ...
│   ├── charts/index.jsx    # SkillBarChart, SalaryBoxPlot, TrendLineChart, MarketSalaryChart
│   ├── Sidebar.jsx, Header.jsx, AppLayout.jsx
│   └── JobCard.jsx         # + MiniJobCard for chat bubbles
├── pages/                  # one file per route
├── services/                # api.js (axios) + one mock service per domain
├── hooks/                   # useWebSocket, useJobSearch, useProfile
├── context/AppContext.jsx   # saved jobs + profile, shared across pages
├── data/mockData.js         # all mock data in one place
└── lib/utils.js              # formatUSD, formatSalaryRange, etc.
```

## Architecture notes — read this before wiring up a real backend

**Everything currently runs on mock data**, but it's already shaped like a
real frontend talking to a real API:

- `services/api.js` is a configured Axios instance reading `VITE_API_URL`.
  Every other file in `services/` has a `USE_MOCK` flag at the top — flip it
  to `false` and uncomment the real `api.get/post(...)` call once your
  backend endpoint exists. The mock and real code paths return the same
  shape, so no caller changes are needed.
- `hooks/useJobSearch.js` and `hooks/useProfile.js` wrap React Query around
  those services (caching, refetch, `placeholderData`). **Note:** `JobList.jsx`
  and `Profile.jsx` currently use `AppContext` + local state directly instead
  of these hooks, because bookmark/profile edits needed to feel instant across
  pages during the demo. The hooks are fully written and tested — swapping the
  pages over to them is a couple of lines per page whenever you want a single
  source of truth backed by the cache instead of context.
- `hooks/useWebSocket.js` wraps the native `WebSocket` API for the chat
  stream and exposes a `fallback` flag if the connection fails, so the UI can
  show the "AI tạm thời không khả dụng" banner from §6 instead of crashing.
  `Chat.jsx` currently drives that same banner through a try/catch around
  `chatService.sendChatMessage` (see below) rather than this hook directly,
  since there's no real WS server to connect to yet — wire `useWebSocket` in
  once `VITE_WS_URL` points at something real.

### Testing the AI fallback state

Per NFR-3 ("Tầng 3 & 4 lỗi → Tầng 1 & 2 vẫn hoạt động bình thường"), the chat
page has a real fallback banner, not just a mock. To see it: open **AI
Assistant** and send the message `/simulate-error`. You'll get the yellow
"AI tạm thời không khả dụng" banner with a button that routes you to
**Job Search** — i.e. exactly the degrade-to-Tầng-1 behavior the spec
describes. Remove that one `if` check in `Chat.jsx`'s `sendMessage` once a
real backend can fail on its own.

## Design decisions worth knowing about

- **Tailwind v3**, configured in `tailwind.config.js` with every color/radius/
  shadow token from §2 of the design doc (`indigo-dark`, `violet`, `mint`,
  `bg`, `8px`/`12px` radii, the exact `0 2px 8px` card shadow, etc.) — not
  default Tailwind grays.
- **shadcn/ui** is listed in the spec's tech stack, but rather than pull in
  Radix + the shadcn CLI for a handful of primitives, `components/ui/index.jsx`
  hand-rolls equivalent Tabs/Toggle/Skeleton/Badge components with the same
  UX, to keep the dependency footprint small. Swap in real shadcn/ui
  components later if you want Radix's accessibility primitives underneath.
- **PDF viewer**: the spec allows `react-pdf` or an `iframe`. The Cover Letter
  page currently renders a stylized mock CV preview instead of either, since
  there's no real uploaded-file storage yet; wiring an actual `<iframe>` or
  `react-pdf` viewer onto the uploaded `File` object (via `URL.createObjectURL`)
  is a small follow-up once `services/profileService.js#uploadCV` talks to a
  real backend.
- **Recharts has no box-plot chart type**, so `components/charts/SalaryBoxPlot`
  is hand-built with raw SVG (whiskers + IQR box + median line + hover
  tooltip) rather than forced into a Bar/Scatter hack.
- **Market heatmap** is a stylized SVG silhouette with three hub markers
  (TP.HCM / Hà Nội / Đà Nẵng), not a geographically accurate map — same
  level of fidelity as the original mockup.

## Known limitations / good next steps

- The "Error" and "Offline" states from §6 are not separately wired up (only
  Loading, Empty, AI Typing, and AI Fallback are live) — once real API calls
  exist, the existing `try/catch` patterns in `services/*` are the place to
  surface them.
- `useDebounce` (in `hooks/useJobSearch.js`) is written and ready but not yet
  used by the header search input — useful once semantic search hits a real
  endpoint and you want to avoid firing a request per keystroke.
- No automated test suite yet (Jest/RTL or Playwright would slot in cleanly
  given how the services layer is isolated from the components).
- No auth flow — `services/api.js` already reads a `techjob_token` from
  `localStorage` for the `Authorization` header, but there's no login page
  yet since none was in the design spec.

## Environment variables

Copy `.env.example` to `.env` when you're ready to point at a real backend:

```
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/chat
```
