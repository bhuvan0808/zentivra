# Zentivra Frontend

Modern Next.js dashboard for the Frontier AI Radar system.

## Stack

- Next.js 16 + React 19
- Tailwind CSS v4
- shadcn/ui (stone base theme)
- Framer Motion (page transitions)
- `next-themes` for light/dark mode

## Pages

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

- `/` Dashboard
- `/sources` Sources manager (full CRUD)
- `/runs` Runs history
- `/runs/[runId]` Run detail + logs/failures
- `/findings` Findings explorer (filters + detail pane)
- `/digests` Digest archive + PDF download
- `/digests/[digestId]` Digest detail
- `/bonus` Bonus view index
- `/bonus/diff-viewer` What changed comparison
- `/bonus/leaderboard` SOTA-style rankings
- `/bonus/entity-heatmap` Entity density matrix

## Environment

Create `.env.local` in this folder:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

If not set, the app falls back to `http://localhost:8000`.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Validation and error handling

- API errors are normalized in `src/lib/api/errors.ts`.
- Response message priority:
  1. `message`
  2. `detail` (string)
  3. `detail[]` validation entries mapped to field errors
- UI validations include user-friendly messages (for example max character constraints and invalid URL format).

## Notes

- Keep backend CORS aligned with frontend origin (`http://localhost:3000` by default).
- Digest PDF downloads use `/api/digests/{digest_id}/pdf`.
