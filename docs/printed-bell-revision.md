# Printed bell and front-face electronics revision

**September 13 owner-authorized engineering work.** The successful T8 fit
assembly at `fefa8bce4e02f1c6c216f7053fb5d7abb16f3d44` remains preserved.
The [dated design inputs](design-inputs/2026-09-13-printed-bell.json) distinguish
owner requests, working CAD selections and unclosed qualification gates.

## Approved direction

Use a single-piece, original printed bell shell around a removable cartridge
with a flush or recessed grille. Retain the successful speaker/yoke/PCB/cell
interfaces where practical. A separate black printed handle is the first
implementation, with a common attachment concept for a later wooden handle.
Do not include a broad handguard disk.

The supplied photographs guide only the generic flared handbell character.
They are not dimensional evidence, traced profiles or licensed assets for
redistribution. Neither image nor its artwork is imported into this project.

The owner is interested in ERYONE silk PLA and is willing to trade print time
for fine layers and exterior finish. Material processing guidance must retain
its source and scope; appearance is not structural or thermal qualification.
The [material and handle source notes](printed-bell-material-and-handle.md)
record the manufacturer's actual ranges, TDS limitations and working M4
fastener dimensions.

## Shared mechanical/electrical interface

The new z0 is the external grille/mouth plane. Initially keep the existing
speaker-relative stack: speaker front z4.5, magnet rear z23.5, PCB F z25.0
and PCB B z26.6. The cell centre remains z36.38, reflecting the nominal
9.78 mm contact datum above B. Removing the old cradle floor alone does not
change the metal contact's working height.

Try the 43 mm PCB first and retain the two existing M2 mounting holes.
Any enlargement must be supported by a coherent electrical floorplan and
reported against the original maximum outer envelope. The custom shell is
not a reason to make every part larger.

Consolidate the electronic SMT population on the speaker-facing side where
possible. The two B-side Keystone SMT contacts remain fitted components and
assembly work; this must not be advertised as a single-side reflow BOM without
an explicit contact-attachment process.

A central M4 machine screw, broad washer and captive metal nut is the working
printed-handle selection. It is similar in size class to an 8-32 screw but not
thread-compatible. Use a keyed locating shoulder and a shell load path clear
of the battery. A wood-screw option is not qualified by a printed nut pocket.

## Completion sequence

1. Produce a separate native front-electronics placement and exact interface.
2. Bind a new FreeCAD shell, cartridge and handle to that interface, including
   both installed and service/plug paths.
3. Once those interfaces are stable, begin justified critical PCB routing.
   Preserve any unresolved native findings and electrical limits.
4. Publish native models, original rendered views, inert print files, a
   reproducible handoff and linked epic updates.

Final placement and routing status, dimensions, screw engagement and measured
or modeled findings will be recorded below when available. No fabrication,
live-cell or child-use approval follows from this engineering iteration.

Owning epics: E04/#4 electrical, E05/#5 mechanics, E07/#7 placement/routing,
E10/#10 eventual qualification.
