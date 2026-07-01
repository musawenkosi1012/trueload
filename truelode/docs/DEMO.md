# Two-minute demo script (Accra stage)

Pre-seeded: Bikita mine → Norton plant corridor, one tipper, one login per role.

1. **Mine** (`mine@truelode.test`) → *Mine* dashboard.
   Set 30 t, grade 1.5%, hit **Weigh out & create batch**.
   → A batch is born (`TL-…`), QR minted, state `IN_TRANSIT`. One line on the ledger.

2. **Transporter** (`transporter@truelode.test`) → *Transporter* dashboard.
   Pick the trip. Hit **Send on-route ping** → blue dot on the corridor, no alert.
   Hit **Send off-route ping** → red dot leaves the green corridor, **OFF_ROUTE alert
   fires live** (no refresh). That's where rock gets swapped — and it's caught.

3. **Processor** (`processor@truelode.test`) → *Processor* dashboard.
   Paste the batch id. **Weigh in** at 34 t → mass balance turns **red (FAIL): +4000 kg**.
   Someone shovelled in untracked rock; the numbers expose it.
   Then **Process → child batch** (4 t product, 11% Li₂O, 20 drums) → child batch +
   parent linked + closed. **Issue passport** → get a QR token.

4. **Verify** — open `/verify/<token>` (or scan from the *Buyer* dashboard).
   The passport story card: 30 t ore → tiny battery-grade product, the full lineage
   back to the mine, the checks it passed, **signature valid + ledger intact**.
   Every drum from this batch carries this one QR → this one origin story.

5. **Regulator** (`regulator@truelode.test`) → watch all of the above land live on the
   corridor-wide alerts feed and the append-only ledger.

**The line to say:** *"A large part of the value Zimbabwe gives away is trust, not
chemistry. Trust is value addition you can build in software — and here it is running."*
