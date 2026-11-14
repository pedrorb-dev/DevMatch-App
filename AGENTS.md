# AGENTS.md

Expo SDK 58 (React Native 0.88, React 19.3, TypeScript ~6.0.3) mobile app — currently the
stock `create-expo-app` TypeScript template. Package manager is **npm**
(`package-lock.json` present; no `bun.lock`).

## Current state vs. README (read this first)

`README.md` describes a planned app (feature-based `src/`, Expo Router, Supabase, a
Python/Scrapy scraper, GitHub Actions). **None of it exists yet.** The real source is only:

- `App.tsx` — root component and actual entrypoint (via `index.ts` → `registerRootComponent`).
- `index.ts` — registration only.

There is no `src/`, no `app/`, no `expo-router`, no Supabase/MMKV/TanStack deps, no scraper,
no `.github/`, and no ESLint or Jest config. Treat the README's folder structure and data
model as a *target spec*, not a map of current files — verify the tree before writing code.

## Commands

```bash
npx expo start          # dev server
npx tsc --noEmit        # typecheck (the only verification; no lint/test configured)
npx expo install <pkg>  # ALWAYS add Expo deps this way, not `npm install` (SDK-compatible versions)
npx expo-doctor         # diagnose dependency/config issues
```

No `lint` or `test` script exists — do not run `expo lint`.

## Expo SDK 58 — don't trust training data

Expo ships breaking changes every release. Before touching any Expo/React Native API, read the
`expo` major version from `package.json` and fetch the matching docs
(`https://docs.expo.dev/versions/v58.0.0/`) or `https://docs.expo.dev/llms.txt`. Never answer
from memory.

## Native & config

- No `ios/`/`android/` directories — they're generated (CNG). Configure native behavior in
  `app.json` + config plugins; never create/edit native folders by hand.
- Expo Go only bundles its native modules. Adding a library with native code requires a
  development build (`npx expo run:ios|android`, or `eas build --profile development`).
- No `eas.json` / EAS config is set up yet.
