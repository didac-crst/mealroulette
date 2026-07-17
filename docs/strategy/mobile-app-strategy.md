# Mobile App Strategy

## Document metadata

- **Purpose:** Strategy for mobile-first web, PWA, Capacitor, and possible future native clients.
- **Authority:** Strategy document. It is not a commitment to build a native app.
- **Status:** Planning assumptions — implementation not started.
- **Update when:** Mobile usage proves a bottleneck, PWA work starts, Capacitor is prototyped, or app-store distribution becomes a concrete goal.

---

## Decision

MealRoulette remains web-first for product validation.

Native mobile is deferred until mobile usage or native-only capabilities become a proven bottleneck.

Preferred progression:

```text
Mobile-first responsive web
  -> installable PWA
  -> Capacitor native shell
  -> React Native / Expo only if proven necessary
```

AI may accelerate native implementation, but it does not remove app-store, signing, device testing, release, support, and long-term multi-client maintenance costs.

## Why Not Native Yet

The current product risks are not native-client risks.

The important validation questions are:

- Can unrelated households onboard?
- Can they build enough recipes?
- Does roulette remain useful after several weeks?
- Do shopping, review, leftovers, and use-soon flows reduce real mental load?
- Does AI recipe entry reduce setup friction?

A native app improves delivery of proven workflows. It does not prove those workflows are valuable.

## Native Value Areas

Native may eventually add value around:

- push notifications;
- reliable local timers and background alerts;
- camera/photo recipe import;
- barcode scanning;
- offline or weak-network shopping mode;
- home-screen widgets;
- share-sheet recipe import from websites;
- smoother mobile navigation and gestures;
- app-store discovery and trust.

These are future-value features, not requirements for the next product validation step.

## Path 1 — Improve Mobile Web

Immediate priority:

- excellent iPhone and Android layout;
- safe-area support;
- large touch targets;
- fast loading;
- stable authentication;
- no horizontal overflow;
- usable cooking mode;
- responsive planning, review, shopping, and settings flows.

This keeps one frontend and avoids premature release complexity.

## Path 2 — PWA

PWA work may add:

- web manifest;
- service worker;
- app icons;
- home-screen install guidance;
- offline shell;
- asset caching;
- web push where practical;
- update handling.

PWA limitations:

- iPhone installation is not obvious;
- push permission UX is awkward;
- background behavior is constrained;
- native share-sheet, widgets, and camera workflows are weaker than native;
- users may still perceive it as a website.

Do not assume PWA push is as reliable as native local/push notifications. Telegram, email, and browser alerts should remain available.

## Path 3 — Capacitor

Capacitor is the preferred first native experiment if app-store distribution or native APIs become useful.

Architecture:

```text
Current React/Vite UI
  -> Capacitor shell
      -> iOS app
      -> Android app
```

Potential first native capabilities:

1. push/local notifications;
2. share-to-MealRoulette recipe import.

Other possible additions:

- haptics;
- camera;
- secure token storage;
- local notifications for timers;
- app badges.

Risks:

- still fundamentally a web UI in a native runtime;
- keyboard, scrolling, safe-area, and navigation issues require testing;
- plugin dependencies add native build complexity;
- app-store submission and signing remain real work.

## Path 4 — React Native / Expo

React Native / Expo is a separate product investment.

Reusable:

- TypeScript types;
- API client;
- validation schemas;
- authentication concepts;
- domain models;
- some hooks/state management.

Mostly rewritten:

- layouts;
- forms;
- navigation;
- CSS;
- dialogs;
- tables;
- mobile interactions.

Choose this only when one or more are true:

- most active usage is mobile;
- PWA installation blocks adoption;
- native capabilities are central to retention;
- Capacitor UX is visibly inadequate;
- there is enough user/revenue/support evidence to justify two clients.

## Architectural Preparation

Prepare for possible native clients without restructuring prematurely.

Do:

- keep backend API-first;
- keep business rules in backend/services;
- keep API contracts stable and typed;
- avoid browser-only authentication assumptions;
- make entities deep-linkable;
- maintain a notification abstraction;
- keep domain logic out of React components where practical.

Do not yet create:

```text
clients/web
clients/mobile
packages/api-client
packages/domain-types
```

until a real second client exists.

## Future Roadmap Note

Potential future mobile-distribution work:

- PWA installability;
- web push where practical;
- Capacitor prototype for native notifications and share-sheet recipe import;
- React Native only after usage proves the need.

## Review Triggers

Revisit this strategy when:

- more than 70% of active use is mobile;
- users repeatedly fail to install or return to the web app;
- timers/notifications are a top retention problem;
- share-sheet recipe import becomes a top onboarding need;
- public beta users explicitly ask for app-store installation;
- Capacitor prototype cost is justified by retention or onboarding evidence.
