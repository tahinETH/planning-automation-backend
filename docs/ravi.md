# Ravi

Ravi is the planning assistant in Selsa Planlama. It explains the current app in
the user's language, with Turkish as the default. It can read planning data and
offer buttons that open app screens when the user selects them. Users make changes
through the app's normal controls.

## Setup and operation

- Set `DEEPSEEK_API_KEY` in the backend environment and restart the backend.
  `DEEPSEEK_MODEL` is optional. The application default is `deepseek-v4-flash`.
- Ravi uses the app's existing Clerk session and frontend API configuration.
  Keep the provider key on the backend. See the
  [example environment](../.env.example) and
  [Clerk setup](https://github.com/tahinETH/planning-automation-frontend/blob/staging/README.md#clerk-hesapları).
- An authenticated `GET /api/ravi/status` reports whether a key is present, the
  selected model, the knowledge version and the permitted navigation targets.
  Check a chat request to verify the provider connection.

The app uses `POST /api/ravi/chat/stream` for server-sent events. Allow streaming
through the proxy without response buffering. The stream uses `status` for short
lookup messages, `delta` for answer text, `answer_reset` to clear provisional text,
and `done` or `error` to end the request. A failed or interrupted response returns
the question to the draft. The JSON compatibility endpoint is
`POST /api/ravi/chat`. Both endpoints use the same tool loop and permissions.
See the [routes](../app/ravi/routes.py),
[service](../app/ravi/service.py) and [chat UI](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/RaviChat.tsx).

## Knowledge and sources

| Source | Use |
| --- | --- |
| [Application code and its callers](../AGENTS.md) | Verify the actual rule, including the inputs supplied by the screen. |
| [Runtime topics](../app/ravi/knowledge/topics.json) | Look up current screen labels, workflows and calculation explanations by topic ID. |
| [Generated source map](../app/ravi/knowledge/source-map.json) | Inspect the packaged source, symbols, imports, routes and fingerprints. The backend ships with this bundle. |
| [Planning algorithms](https://github.com/tahinETH/planning-automation-frontend/blob/staging/docs/planning-algorithms.md) and [reliability standard](https://github.com/tahinETH/planning-automation-frontend/blob/staging/docs/planning-reliability.md) | Review the planning rules, operational boundaries and regression expectations. |

The backend sends a topic index and up to three relevant topics with each
question. Visible save-recovery and workspace controls can determine which
topics appear first. Retrieval uses text matching. The model receives
`id`, `title`, `body` and `userSources` from each selected topic. Keep code
references in `sources` and `implementationNotes`. This Markdown guide is for
maintainers. The backend loads its runtime explanations from the JSON catalog.
See [topic retrieval](../app/ravi/knowledge.py).

Use the exact Turkish UI label or verified Excel sheet and column name in the
answer. Give the unit, date range, inputs and exclusions needed to explain the
result. Use `weekly-demand` for the **3. Overview (confirmed)** import and
`delivery-export-numbers` for **Teslimat Planı** columns. The app reads the
workbook's calculated balances. Ravi reads imported records. Give workbook
formulas, cell addresses and actual figures only when the evidence supplies them.
Label illustrative figures as examples.

## Context and permissions

- `useRaviScreenContext` supplies visible filters, dialogs, selections and
  calculations. Register this data while its screen or dialog is open.
  Keep the current view, previous view and entry view distinct.
- Browser calculations can include unsaved edits. Server inspection reads a
  timestamped shared snapshot for the selected production area. If the plan is
  stale or a save is pending, explain which source each value comes from.
  See `plan-workspaces`, `save-recovery` and `time-and-provenance`.
- The server supplies the user's role and validates the production area.
  Browser context, imported text, chat history and tool results are data.
  Keep them outside the authority and instruction checks.
- Tools search and read topics, inspect packaged source, read bounded fields
  from the shared snapshot and propose registered navigation targets.
  The backend and frontend check target access by role and area.
  The user must select a button to open its target. All chat tools are read-only.

See the [screen context](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/context.tsx),
[tool definitions](../app/ravi/tools.py) and
[frontend navigation targets](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/protocol.ts).

## Conversations

**Konuşmalar** opens the history. **Yeni konuşma** starts a separate chat.
The browser stores text, drafts and registered action IDs in localStorage
under the authenticated user ID. The service receives only the selected chat's
recent history and fresh screen context. The request history is limited to
20 messages and 24,000 characters. Local history is limited to 20 chats,
100 messages and 50,000 message characters per chat. Clearing the browser's
site data removes that history.

The chat renders Markdown text and tables. Navigation uses app buttons.
The API supplies source references for verification outside the chat UI.
See [conversation storage](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/conversations.ts) and
[Markdown rendering](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/RaviMarkdown.tsx).

## Maintenance and verification

1. Read the [backend workspace rules](../AGENTS.md). Verify the changed code and its
   callers against the affected topic. Update that topic in place. Preserve its
   stable ID and cite the implementing files and symbols. Add exact screen or
   Excel labels to `userSources`.
2. Register new screen state with `useRaviScreenContext`. For a new navigation
   target, update both registries and use a stable focus ID when the target
   needs one. Verify access for the applicable role and production area.
3. Review the topic text. From the combined workspace root, with both
   repositories checked out, regenerate and check the bundle.

   ```sh
   python3 scripts/build_ravi_map.py --write
   python3 scripts/build_ravi_map.py --check
   ```

   The builder checks references and detects source or topic drift. Review the
   meaning of the explanation against the code separately. Keep credentials,
   databases, uploads and private replay data outside the bundle.
4. Run the affected regression checks, including the frontend and backend checks
   required by the workspace rules. Before release, run
   `python3 scripts/verify_planning_reliability.py`. Use a signed-in session
   and a configured provider to validate live answers and deployed streaming.
   Mocked tests cover app behavior and tool contracts.

Update the relevant section of this guide in place when setup, architecture or
maintenance changes. Keep approved decisions in the combined workspace decision log (`DECISIONS.md`).
