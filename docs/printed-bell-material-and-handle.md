# Printed-bell material and handle source notes

**2026-09-13 source review, not a qualified print profile or strength rating.**
This supports the [printed-bell revision](printed-bell-revision.md).

## ERYONE silk PLA

The owner linked [Amazon ASIN B082XTFB7T](https://www.amazon.com/dp/B082XTFB7T).
The Amazon page did not expose usable product parameters during this review.
The exact listing/spool-to-formulation mapping therefore remains unconfirmed.
Do not substitute settings for a newer high-speed formulation.

The [manufacturer's standard Silk PLA page](https://www.eryone.com/silk-pla-product/)
lists nozzle **190-220 C**, bed **55-70 C**, speed **30-60 mm/s**, and filament
diameter **1.75 +/-0.03 mm**. The page's linked
[Silk PLA TDS](https://file.globalso.com/file_manage/3828/20251125/eryone-silk-pla-tds.pdf)
identifies itself as **version 1.0, 08/2024**, despite the later URL directory.
The reviewed PDF SHA-256 is:

`0213b4d708b87844989996308e1d0173379ff783be67fd89bab4f4dfe9fa8184`

That TDS repeats the temperature ranges but lists **30-100 mm/s**. Preserve
the difference rather than presenting a single universal speed limit.
It expressly says higher temperature or slower printing can increase sheen;
this supports the owner's proposed direction, but not heating beyond the
actual spool's range. No maximum volumetric flow or layer-height specification
was found in the reviewed TDS.

For a **0.4 mm nozzle and an inert finish/geometry trial**, a project-selected
starting point is **0.12 mm layers, 215 C nozzle, 60 C bed and 30 mm/s outer
walls**, retaining the established first-layer/adhesion settings. These are
unexercised starting settings, not an ERYONE K1C profile. Comparing 0.12 with
0.16 mm layers and 210/215/220 C on a small curved sample can separate visible
layer stepping from gloss and bonding. Do not lower cooling universally or
apply high-speed acceleration/flow limits without looking at the actual
overhangs and print.

Keep the visible shell free of support contact where geometry permits.
Print the shell mouth-down/handle-up, with accessible internal supports or
sloped inner surfaces where needed; print the grille's exterior face on the
bed. Plate texture transfers to that face. Shorter layers do not eliminate
the seam, support marks, or all stair-stepping at a rounded crown.
See [Prusa's geometry/orientation guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135);
its printer-specific overhang capability is not a measured K1C capability.

The TDS gives typical density **1.32 g/cm3**, Vicat **56 C**, heat-distortion
temperature **53 C at 0.45 MPa**, and glass transition **63 C**. None is a
permitted enclosure operating/storage/charging temperature. Its printed
sample table also shows directional strength differences; those data are
not allowable stresses for our handle. In particular, the X-Z tensile row
names GB/T 1843, an impact-test standard, so its standard attribution should
not be treated as verified tensile qualification. The TDS itself says its
values are for reference/comparison, not design specifications.

Use the silk candidate for appearance/fit development. Final shell, mounting
boss and handle suitability still needs impact, creep, temperature and
assembly-load evidence. A black non-silk printed handle can share the same
interface, but a material name alone does not establish its strength.
No vendor PDF or user reference photograph is redistributed here.

## One central handle fastener

The working selection is an **M4 machine screw into a captive metal M4 nut**,
with a locating/keyed shoulder and a large washer inside the crown. This
keeps repeated service out of threads cut directly into printed plastic.
The washer spreads the head load; the shoulder/key transfers lateral and
rotational loads into the shell rather than relying only on clamp friction.
The battery and PCB are not part of this load path.

M4 is close to the size class of the owner's suggested 8-32, while retaining
the metric convention of the existing M2 joints. Threads are not
interchangeable. A 1/4-20 screw would require a larger 6.35 mm nominal bore;
it is not adopted without a demonstrated need.

The following are **supplier-published standard-family dimensions**, not an
inspected licensed ISO standard or a selected hardware lot:

| Item | Working/source dimensions |
|---|---|
| [M4 pan-head screw](https://www.fasteners.eu/standards/ISO/7045/) | The page actually labels its table DIN 7985. Pitch0.7, head diameter7.64-8.00 mm, height2.95-3.25 mm (nominal3.1). M4x16 under-head length15.65-16.35; M4x20 length19.6-20.4 |
| [M4 large washer, DIN 9021](https://www.fasteners.eu/standards/DIN/9021/) | ID4.30-4.48, OD11.57-12.00, thickness0.90-1.10 mm |
| [M4 hex nut, ISO 4032 family](https://www.fasteners.eu/standards/ISO/4032/) | Across flats6.78-7.00, height2.90-3.20 mm, pitch0.7 |

The new mechanical model must select an actual working screw length and
demonstrate nut loading, bearing surfaces, thread engagement, tip clearance,
tool access and battery separation, including relevant dimensional bounds.
A washer/head envelope alone does not prove adequate printed bearing
strength, preload, anti-loosening or service life. Do not over-tighten an
unqualified silk-PLA boss.

A wooden handle remains a later compatible option, not an implemented wood
joint. A predrilled wood-screw pilot depends on screw design, wood species,
grain and engagement; the printed handle's machine-nut dimensions cannot
qualify it. A matching machined tenon and mechanically retained threaded
interface can reuse the shell without altering the PCB.
