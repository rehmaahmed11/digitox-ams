# Engine — instruction log

New guidance from the user is recorded **here first**, then folded into the rule file it affects.
Every production run reads the latest rules — this log keeps the history of *why* they changed.

Format: newest last. One line per instruction: **date — what was told — what changed**.

---

## Log

| Date | Instruction | What changed in the engine |
|---|---|---|
| 2026-10-16 | Set up the production system and divide it into parts: **engine** (all production logic, branding, details — updated whenever new instructions arrive), **software/pc** and **software/mobile**, **promotional-video**, **blogger** (Google posts), and a **theme** folder. Keep it simple to organize. | Created this system: `engine/` (BRAND.md, WORKFLOW.md, this log, specs), `software/pc`, `software/mobile`, `promotional-video/`, `blogger/`, `theme/`. Existing product (*AMS Caps Lock OSD*) moved into its new places. |

---

## How to add an instruction

1. Append a row to the table above.
2. Update the affected rule file:
   - brand / identity / colors / voice → [`BRAND.md`](BRAND.md)
   - production order / folder layout → [`WORKFLOW.md`](WORKFLOW.md)
   - PC software rules → [`software/pc.md`](software/pc.md)
   - mobile software rules → [`software/mobile.md`](software/mobile.md)
   - video rules → [`video.md`](video.md)
   - blog post rules → [`blogger.md`](blogger.md)
   - theme rules → [`theme.md`](theme.md)
3. Leave old products alone unless the user asks to re-produce them.
