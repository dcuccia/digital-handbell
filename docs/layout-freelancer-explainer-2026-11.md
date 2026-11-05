# Paying a human to finish the routing - explainer

Gated fallback in the [routing completion plan](routing-completion-plan-2026-11.md):
nothing is posted, contacted or paid until the owner says so. Prices below
are published or reported figures gathered November 2026; treat them as
planning ranges, not quotes.

## What kinds of help exist

| Option | How it works | Reported price | Turnaround | Fit for us |
|---|---|---|---|---|
| **JLCPCB layout service** | Upload project, priced per pin | About $0.46-0.73 per pin, $100 minimum | ~3 days simple jobs | Transparent backstop. Whole-board pin count (325 pads) suggests roughly $150-240 if they price the full board, less if only the remaining work is priced. |
| **PCBWay layout service** | Upload, custom quote; supports KiCad | No public list; small jobs reportedly ~$80-200 | Negotiated | Good KiCad support; quote is free. |
| **Upwork / Fiverr freelancers** | Fixed-price job, platform escrow | Mostly $30-70/hour; small fixed jobs commonly $75-300 | 1-5 days once started | Best control over scope and payment milestones. Quality varies; vet reviews and KiCad experience. |
| **Toptal / Malt (vetted seniors)** | Hourly | $60-150+/hour | Fast | Overkill for this size. |
| **KiCad Discord #kicad-jobs, KiCad forum** | Informal posts and replies | Negotiated, often cheapest | Variable | Good for finding an experienced KiCad person; no escrow. |
| **Free review: r/PrintedCircuitBoard, KiCad forum** | Post screenshots for critique | Free | Days | Useful sanity check before paying anyone. |

Sources: JLCPCB layout FAQ, PCBWay layout page, Upwork/Fiverr/Toptal rate
guides and a 2025 KiCad forum hiring thread, all accessed November 2026 by a
research agent. MacroFab and NextPCB mainly build boards rather than finish
layout.

## Realistic budget and success expectations

- **Work size:** about 37 remaining connections. Roughly half are simple
  signals; the rest are power, ground and USB around the RP2040, where the
  board is crowded. With permission to nudge a few small parts, an
  experienced designer should finish this.
- **Budget (my estimate):** plan for about **$150-500**. The research quotes
  $75-300 for marketplace finish jobs; the crowded IC1 area could push the
  work towards the upper end or beyond. JLCPCB's per-pin model gives a
  predictable ceiling.
- **Time:** typically one to five business days after the person starts,
  plus one revision round.
- **Likelihood of success:** high with a competent KiCad designer and clear
  acceptance criteria. Most failures come from vague scope, not the board.

## Common failure modes and how we avoid them

| Risk | Mitigation in our request |
|---|---|
| Designer "improves" placement or reroutes finished areas | List locked parts and copper; allowed moves only within stated regions; our check flags any lost copper. |
| Ignores rules or battery-contact keep-outs | Rules and keep-outs are already in the KiCad files; acceptance is our standard check. |
| Hands back an unverified board | Payment milestone tied to zero unconnected items and passing the check. |
| Licensing confusion | The design is open source (CC BY-SA hardware); state that deliverables are released under the same terms. |
| Scope creep and extra charges | Fixed price, two revision rounds, escrow through the platform. |

## What we would send (agent prepares it)

The frozen KiCad 10 project, the remaining-connection list, the movable
parts and allowed regions, stackup and rules, the battery-contact and
private-return constraints in plain language, mechanical keep-outs, and the
exact acceptance check. Deliverables: native KiCad files only, with every
part move listed.

## Recommended order if we get here

1. Free review post (r/PrintedCircuitBoard or KiCad forum) to catch obvious
   placement problems.
2. In parallel, request quotes from one or two Fiverr/Upwork KiCad designers,
   PCBWay, and the JLCPCB layout service as a priced backstop.
3. Choose by price, KiCad experience and willingness to accept our check as
   the completion criterion. Owner approves before any payment.
