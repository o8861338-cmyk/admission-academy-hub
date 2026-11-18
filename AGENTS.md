<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->
## Project rules
- Academic trainer portal lives in `src/modules/academic`, routes `src/routes/academic.*.tsx`, CSS scoped under `.academic-module`, saved state loaded after hydration.
- Finance lives in `src/modules/finance`, with routes `src/routes/finance.*.tsx` and CSS scoped under `.finance-module`.
- Admin lives in `src/modules/admin`, with routes `src/routes/admin.*.tsx` and CSS scoped under `.admin-module`.
- App data (admissions, leads, HR, marketing state) persists in browser localStorage via `src/lib/local-app-state.ts`, an `app_state`-shaped shim; swap that module for a real table if shared multi-device data is needed, since callers already use the table-style API.
- tsconfig keeps noUncheckedIndexedAccess, noPropertyAccessFromIndexSignature and exactOptionalPropertyTypes off because the embedded Admin/Finance/Academic apps were written without them.
- App chrome lives in `src/components/AppShell.tsx` (top pill nav, icon rail, glass backdrop); `<body>` carries `.solvik` so every page and portal gets the dark glass tokens. Module light colours are converted by `scripts/solvik_dark.py`: run `remap` to regenerate `src/styles/solvik-remap.css` after adding Tailwind colour classes, because hard-coded light classes otherwise render light-on-dark. Module CSS files were converted once with its `css` then `accent` modes from their original import (git 251c657), so re-convert from that original, never from an already converted file. Module token and font overrides live at the end of `src/styles.css`.
- Main menu is the macOS Dock-style `src/components/DockNav.tsx` (magnify on pointer via CSS var `--dock-size`, tile colours as `--dock-*` tokens in styles.css); keeps per-frame size updates out of React state to avoid re-renders.
- Every module (Admission, Admin, Finance, Academic, Directors, HR) shows its pages as the underline tab sub menu from `src/components/ModuleTabs.tsx` under the dock, replacing per-module sidebars/drawers, so navigation looks the same everywhere.
