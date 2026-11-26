# Ravi

Ravi is the planning assistant in Selsa Planlama. It explains the current app in
the user's language, with Turkish as the default. It can read planning data and
offer buttons that open app screens when the user selects them. Users make changes
through the app's normal controls.

## Setup and operation

- Set `DEEPSEEK_API_KEY` in the backend environment and restart the backend.
  Optionally set `OPEN_ROUTER_API_KEY` (or `OPENROUTER_API_KEY`) as a fallback
  provider routed through OpenRouter (`deepseek/deepseek-v4-flash`) whenever
  `DEEPSEEK_API_KEY` is unset or returns an HTTP/billing error (such as `402`).
  `DEEPSEEK_MODEL` is optional. The application default is `deepseek-v4-flash`.
  Provider requests omit `max_tokens` (leaving output length to the provider
  default while keeping Ravi's bounded 12,000-character answer limit). Direct
  DeepSeek requests pass `thinking: {"type": "disabled"}`, while OpenRouter
  requests pass `reasoning: {"enabled": false}` so OpenRouter does not silently
  run hidden reasoning tokens. Empty SSE `data:` frames are skipped, hitting a
  provider length or response size cap surfaces an explicit `response cap reached`
  error to the user, and provider failures/timeouts emit metadata-only server
  warnings without logging prompts, responses or credentials.
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
topics appear first. Retrieval uses text matching and boosts `app-navigation`
and matching topics for short/informal Turkish navigation cues (such as `git`,
`aç`, `yer`, `nerede`, `götür`, `sekme`, `düğme`, `buton`, `ekran`, `alan`,
`ayar`, `tatil`, `bakım`), while keeping unmatched queries empty. The model receives
`id`, `title`, `body` and `userSources` from each selected topic. Keep code
references in `sources` and `implementationNotes`. This Markdown guide is for
maintainers. The backend loads its runtime explanations from the JSON catalog.
See [topic retrieval](../app/ravi/knowledge.py).

Use the exact Turkish UI label or verified Excel sheet and column name in the
answer. Responses are brief-first by default: 1–3 short sentences or up to 3 short
bullets for ordinary and navigation questions, and a concise source/formula/unit/rule
summary (2–4 short lines or bullets) for calculation questions, expanding into full
step-by-step walkthroughs or illustrative examples when requested (for example via
**Detaylı açıkla**). Give the unit, date range, inputs and exclusions needed to explain the
result. Use `weekly-demand` for the **3. Overview (confirmed)** import and
`delivery-export-numbers` for **Teslimat Planı** columns. The app reads the
workbook's calculated balances. Ravi reads imported records. Give workbook
formulas, cell addresses and actual figures only when the evidence supplies them.
Label illustrative figures as examples.

## Context and permissions

- `useRaviScreenContext` supplies visible filters, dialogs, selections and
  calculations. Register this data while its screen or dialog is open.
  `RaviContextProvider` also accepts a lazy `getPlanningDetails` callback invoked
  only when Ravi reads browser context: `PlanningApplication` supplies
  `planning.liveSchedule` via `buildRaviScheduleDigest` (bounded `<= 21,000`
  chars of `downstreamGaps` with `before`/`after`/predecessor timing and calendar
  pauses, `downstreamResources`, and `turningMachines`), while `PlanBoard` and
  `MachinesView` expose memoized active-process gaps (`processBoard` /
  `resourceSchedule`) so Ravi can diagnose Gantt/machine gaps without requiring
  the user to click a specific bar first.
  Keep the current view, previous view and entry view distinct. Live screen
  context badges in the chat panel reflect the active screen state.
- Browser calculations can include unsaved edits. Server inspection reads a
  timestamped shared snapshot for the selected production area. If the plan is
  stale or a save is pending, explain which source each value comes from.
  See `plan-workspaces`, `save-recovery` and `time-and-provenance`.
- The server supplies the user's role and validates the production area.
  Browser context, imported text, chat history and tool results are data.
  Keep them outside the authority and instruction checks.
- Tools search and read topics, inspect packaged source, read bounded fields
  from the shared snapshot and propose registered navigation targets.
  The expanded navigation registry covers screens, focus targets and panels:
  Planlama tools (**Planı Çalıştır**, **Plan tavsiyeleri**, **Tezgah dolulukları**),
  Siparişler tools (**Excel geçmişi**, **Tip ekle**, and Çubuk Filtre's **Aylık ihtiyaç**
  and **Başlangıç stoklarını uzlaştır**), admin-only Ayarlar sub-tabs (**Stok ayarları**,
  **Setup ayarları** [Torna], **Resmi tatiller**, **Bakımlar**, **Mesai ve vardiya**),
  Genel Bakış (**Saha planı indir**), **Uygulama güncellemeleri**, and the `guide`
  (**Sayfa rehberi**) and `tour` (**Tanıtımı başlat**) panels.
  The backend and frontend check target access by role and area.
  Navigation is strictly click-only: the user must select the **"Beni oraya götür"**
  button to open its target (`executed: False`). Production area switching
  (`Piston` ↔ `Çubuk Filtre`) is never automatic; when a user asks for a feature in
  the other area, Ravi states the active area, reminds them to verify their workspace
  save status, and offers the manual **Sol panel → Üretim alanı** (`production-area`)
  target. When a control or section only appears conditionally (such as recovery
  actions on error/conflict in **Plan çalışma alanı**, **Başlangıç stoklarını
  uzlaştır** when opening-stock data is loaded, or **Otomatik planla karşılaştır**
  under **Planlama → Planlama araçları** only when a saved automatic-plan snapshot
  exists, manual edits were made, and `Değişiklik var` (`dirty`) is inactive),
  Ravi names the host screen and button, explicitly states the condition under
  which it becomes visible, and offers the navigation button to the host
  screen/card. All chat tools are read-only. If the provider emits raw DSML
  tool-call markup in text, `service.py` parses and executes valid invocations and
  strips DSML tags before sending `done`.

See the [screen context](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/context.tsx),
[tool definitions](../app/ravi/tools.py) and
[frontend navigation targets](https://github.com/tahinETH/planning-automation-frontend/blob/staging/features/ravi/protocol.ts).

## Conversations

**Konuşmalar** opens the history. **Yeni konuşma** starts a separate chat.
The chat header and message controls also include **Durdur** (stops an in-flight
stream without saving an incomplete answer), **Geniş görünüm** (toggles a wider
panel layout), **Önceki ekrana dön** (returns to the previous screen after
clicking a navigation card), and **Detaylı açıkla** (requests a fuller breakdown
of a brief answer).
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

## Personal draft sidebar

Open **Kişisel taslak → Kademeli planlama** while stages remain. The sidebar
shows the last planned process and the next process. **Sonraki prosesi planla**
and **Tüm prosesi planla** use the existing worker and open the first new Gantt
tab. Calculation and save status are shown separately.

**Ortak plana dön** is below **Ortak plan yayını** or **Yöneticiyle paylaş**.
The button waits for the calculation and save. If the shared plan read fails,
the personal draft stays open. **Senaryolar → Planlarım → Yükle** can reopen the
saved draft after a successful return.

## Local production refresh

The loopback runner accepts `--production-sync`. It reads the backend's
`PRODUCTION_API_URL` and `PRODUCTION_SYNC_TOKEN` from its environment or local
configuration. The token stays in the backend. In the local test administrator
session, **Ortak plan → Diğer işlemler → Prod’dan güncelle** opens the same
review as staging and labels the destination **yerel kopya**. An empty copy may
take its first reviewed snapshot. The current deployed source must serve the
selected area. The preview and conflict checks run before the local write.

## Çubuk Filtre review and deadlines

**Seçenekleri karşılaştır** includes **Standart planlama**. All four rows use
the complete route for deadline coverage, including the correct delivery wait.
**Aylık talep terminleri** shows the existing checkpoints for monthly demand.
**Gelecek haftadan** appears with a weekly customer source.

**Tavsiyeler ve uyarılar** includes **Hareketsiz şarjlar** and **Pasif atamada
bekleyen işler** in both production areas. If a downstream placement makes
good-piece coverage worse at a Çubuk Filtre deadline, **Termin uyarısı** appears
before apply. A saved Filter draft restores its scenario name on reload.

## Çubuk Filtre shop-floor work and calendars

**Beklemeyi tamamla** for external processing releases the open lot to its next
queue at confirmation time. Prior actual work and the lot quantity stay recorded.
**Adedi düzenle** shows the count time and the calculated finish for a current
downstream job. The observation uses Türkiye time.

**Kalan üretimi iptal et** is available on eligible single Torna jobs and
protected remainders. **Üretim iptalleri** and **İptal sonrası inceleme** show
the selected area's records. In monthly Filter demand, the review holds the
expected good-piece loss while the production record stores physical pieces.
Shared charge portions are outside this flow.

**Takvim** shows the CF-BEKLEME, CF-KALITE and CF-DEMAND normal shifts.
A planner can filter their records. An administrator can add a dated holiday shift
in **Ortak plan**.

## Çubuk Filtre Batch 5

**Prod’dan güncelle** keeps the monthly delivery baselines in the
**Siparişler** group. **Tam yedek (Parametreler ve Ayarlar)** supports both
areas for administrators. Visible Filter sheets show the stock inputs,
calendar shifts and product settings. The hidden payload is the restore
source. **Senaryolar → Seçilenleri indir** uses authorized saved records
and gives Filter all eight process sheets.

**Günlük Sevkiyat Planı yükle** and **Üretim talebini yükle** (Piston retains **Müşteri Excel’ini yükle**) are separate
controls in Filter. The selected source is applied after review. Ravi offers
area-specific suggestions and navigation. Both areas share feedback and app
updates. Plan and scenario data remain scoped to the selected area.

## Personal draft WIP moves, over-planned completions & bulk reset (2026-11-26)

- In **Kişisel taslak**, only currently running downstream jobs (`Mevcut üretim`) stay locked to shared production; queued WIP (`Yarı mamül`) machine transfers, queue edits and automatic resets persist through save, reload and publication.
- **Siparişler → İçe / dışa aktar → Teslimat planını indir** (and Piston's **CNC + 3 gün**) also works in **Kişisel taslak** via server-verified composition of the saved draft with shared live facts (`Kişisel taslak` badge and `Taslak` filename).
- **Fiili tamamlanan adet** on Torna and downstream completion flows can exceed planned/available quantity; any quantity different from planned/available asks for explicit **Evet / Hayır** confirmation.
- **Tüm prosesleri otomatik plana döndür** (in downstream **Planlama** tabs and **Tezgahlar → Tezgah işlemleri**) clears manual overrides across all downstream processes in one undoable step without touching Torna or active running jobs.
