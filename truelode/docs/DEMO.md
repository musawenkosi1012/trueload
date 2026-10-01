# Two-minute demo script

Pre-seeded: Bikita ASM Co-op mine → Norton Sulphate Plant corridor, Sango Haulage
tipper (ABZ-1234, T. Moyo), one login per role. Custody moves by QR: mine →
transporter → plant, and every step below is clickable through the UI.

1. **Mine** (`mine@truelode.test`) → *Load ticket* tab.
   Set 30 t, grade 1.5%, hit **Weigh out & create batch**.
   → A batch is born (`TL-…`), QR minted, state `IN_TRANSIT`. One line on the ledger.
   Then **Hand to transporter:** select *Sango Haulage* → **Offer handover**.
   Leave the QR on screen — the driver needs the token.

2. **Transporter** (`transporter@truelode.test`) → *Trips* tab.
   **Pending pickups** → **Accept custody** → paste the batch QR token → confirm.
   Pick the trip. Hit **On-route ping** → blue dot on the corridor, no alert.
   Hit **Off-route ping** → red dot leaves the green corridor, **OFF_ROUTE alert
   fires live** (no refresh). That's where rock gets swapped — and it's caught.

3. **Transporter**, same tab: **At the plant gate? Hand the batch to the processor**
   → select *Norton Lithium Plant* → **Offer handover**.

4. **Processor** (`processor@truelode.test`) → *Process* tab.
   **Pending deliveries** → **Accept custody** → paste the batch QR token → confirm.
   Paste the batch code (`TL-…`). **Weigh in** at 34 t → mass balance turns
   **red (FAIL): +4000 kg**. Someone shovelled in untracked rock; the numbers
   expose it — and a HIGH WEIGHT_MISMATCH flag lands on the ledger for the
   regulator. Re-weigh at the true 30 t → **PASS**, state RECEIVED (the flag
   stays on the record; processing proceeds).
   Then **Process → child batch** (4 t product, 11% Li₂O, 20 drums) → child batch +
   parent linked. **Issue passport** → get a QR token.

5. **Verify** — open `/verify/<token>` (or scan from the *Buyer* dashboard).
   The passport story card: 30 t ore → tiny battery-grade product, the full lineage
   back to the mine, the checks it passed, **signature valid + ledger intact**.
   Every drum from this batch carries this one QR → this one origin story.

6. **Regulator** (`regulator@truelode.test`) → watch all of the above land live on the
   corridor-wide alerts feed and the append-only ledger — including the three
   custody events (offered / accepted ×2) and the weight-mismatch flag.

**The line to say:** *"A large part of the value Zimbabwe gives away is trust, not
chemistry. Trust is value addition you can build in software — and here it is running."*
