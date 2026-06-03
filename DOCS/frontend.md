# Frontend (`clerk-react/`) — overview

The frontend is a small **React + Vite + Clerk** application. At the moment it
mainly wires authentication and shared API behavior; the repo submission and
indexing-progress UI still need to be built on top of these foundations.

## Current structure

```
clerk-react/
├── src/
│   ├── main.tsx       App entry. Loads ClerkProvider.
│   ├── App.tsx        Shows Sign In / Sign Up / User button and installs auth interceptor.
│   └── libs/api.ts    Shared Axios instance + Bearer-token interceptor.
├── index.html
├── vite.config.ts
└── package.json
```

## Auth flow

`src/main.tsx` reads `VITE_CLERK_PUBLISHABLE_KEY` and wraps the app in
`<ClerkProvider>`. If the key is missing, the app throws immediately so the
configuration problem is obvious.

`src/App.tsx` uses Clerk's `useAuth()`:

- while signed out: renders `SignInButton` and `SignUpButton`,
- while signed in: renders `UserButton`,
- once Clerk is loaded and the user is signed in, installs the Axios request
  interceptor from `src/libs/api.ts`.

## API client

`src/libs/api.ts` exports a shared Axios instance:

- `baseURL` comes from `VITE_API_URL`.
- `setupInterceptor(getToken)` attaches `Authorization: Bearer <token>` to every
  outgoing request.
- The setup function returns a cleanup callback that ejects the interceptor when
  the component unmounts or auth state changes.

This is what lets backend endpoints call `authenticate_and_get_user_id()` and
trust Clerk's JWT.

## Environment variables

Create `clerk-react/.env` (or your Vite environment file) with:

```
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_API_URL=http://localhost:8000
```

Vite only exposes variables prefixed with `VITE_` to browser code.

## Running locally

From `clerk-react/`:

```
npm install
npm run dev
```

Other scripts:

- `npm run build` — TypeScript build + production Vite build.
- `npm run lint` — ESLint.
- `npm run preview` — preview the built app.

## Backend endpoints the UI should call

These endpoints already exist in the backend:

- `POST /api/repos` — body `{ "url": "https://github.com/owner/repo" }`; returns
  `status`, `repoId`, `jobId`, and repo metadata.
- `GET /api/repos/{repo_id}` — returns repo metadata and indexing stats.
- `GET /api/tasks/{task_id}` — returns a user-friendly `phase` such as
  `cloning`, `parsing`, `indexed`, or `failed`.

The future UI should submit a repo URL, store the returned `jobId`/`repoId`, then
poll the task endpoint until the phase is `indexed` or `failed`.
