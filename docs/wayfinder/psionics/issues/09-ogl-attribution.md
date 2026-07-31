# 09 — What OGL attribution do we ship, and where?

Type: grilling
Status: resolved
Blocked by: —
Map: [Psionics](../map.md)

## Question

[Ticket 02](02-data-quality-ogl.md) established the obligation and found that we cannot simply copy
the upstream notice: **pf1-psionics' own §15 is incomplete** (missing *Psionics Expanded: Advanced
Psionics Guide*, which the Aegis actually traces to, and *Psionics Augmented: Seventh Path*, which its
own Bond of Death power cites), and the same block is copy-pasted verbatim into `pf1-pow`. Ours has
to be hand-curated from the `sources:` blocks in whatever we actually extract.

Decide four things:

1. **Where the notice lives.** A root `LICENSE` with the full OGL 1.0a text plus a curated §15, the
   way `pf1-pow` does it — or the stricter `pf1spheres` pattern (REUSE.software/SPDX, a
   `LICENSES/LicenseRef-OGL-1.0a.txt`, and a manifest declaring `Backend/json/** → OGL`, keeping our
   own Python separately licensed). The second is more auditable and machine-readable; the first is
   less work.
2. **How §8 marking works** for a repo where OGC and our own code share a tree — is a per-directory
   `NOTICE` / `ATTRIBUTION.md` enough to say "these JSON files are OGC and this Python is not"?
3. **The API question.** An HTTP response carrying extracted mechanics is "Distribution" under §10,
   which requires shipping the licence with every copy. Embedding the full OGL in every payload is
   absurd; a stable `/license` (or `/api/v1/ogl`) endpoint plus a reference in the API docs is the
   proposed alternative. Is that acceptable, and does the payload carry a pointer field?
4. **Whether we credit pf1-psionics itself** as the intermediate compiled source, separate from the
   DSP books.

Also decide the disclaimer text — Paizo Community Use Policy plus a DSP non-endorsement line, the way
both comparable modules do it.

This is a decision about what ships, not a legal opinion. If it turns on something genuinely unclear,
say so in the answer rather than guessing.

## Answer

**The middle path: a root `LICENSE-OGL.txt`, a per-subtree `NOTICE.md`, and a `/license` endpoint.**
More auditable than pf1-pow's single file, less machinery than pf1spheres' full REUSE setup.

**1. Where the notice lives.** Root `LICENSE-OGL.txt` carries the full OGL 1.0a text plus a §15
**hand-curated from the `sources:` blocks in what we actually extracted**. This is not optional
tidiness: [ticket 02](02-data-quality-ogl.md) found upstream's §15 omits *Psionics Expanded: Advanced
Psionics Guide* (which the aegis traces to) and *Psionics Augmented: Seventh Path* (cited by its own
Bond of Death power), and that the same incomplete block is copy-pasted verbatim into pf1-pow.
Copying it would propagate a known-bad notice. The repo's existing `LICENSE` keeps covering our
Python; the OGL file is separate so the two licences are not conflated.

Full REUSE/SPDX was rejected as more ongoing obligation than value here — the manifest has to be kept
accurate as files move, and this repo moves JSON around a lot. If the OGC surface grows past
psionics, revisit.

**2. §8 marking.** A `NOTICE.md` in `Backend/json/class_data/psionics/` declaring that subtree Open
Game Content, and stating that the surrounding Python is Product Identity-free original work under
the repo's own licence. Per-directory marking is enough because the split is clean along a directory
boundary — OGC data in `Backend/json/`, our code everywhere else. It would not be enough if the two
were interleaved in the same files.

**3. The API question.** Yes, the proposed alternative is acceptable. An HTTP response carrying
extracted mechanics is Distribution under §10, but embedding the full licence in every payload is
absurd and would bloat every generated character. `Backend/app.py` serves a stable **`/license`**
route returning the OGL text plus §15, and the payload carries a **pointer field** to it. This is the
same shape every OGL-bearing web tool uses. Flagging honestly: §10's "include a copy of this License
with every copy" is not obviously satisfied by a URL, and this is the one part of the ticket that
turns on something genuinely unsettled rather than a clear reading — the pointer is a considered
position, not a certainty.

**4. Credit `pf1-psionics` itself: yes.** It is the intermediate compiled source we adopted as render
target and read for name reconciliation, and crediting the compiler alongside the original publisher
costs nothing. Named separately from the DSP books so the provenance chain is legible.

**Disclaimer text**, matching what both comparable modules ship: a Paizo Community Use Policy notice,
and a line stating this project is not affiliated with or endorsed by Dreamscarred Press.

Note that no *new* obligation is created by the wiki being our source of truth — the Metzofitz wiki
is a republication of Ultimate Psionics, so the §15 chain runs to the DSP books either way.
