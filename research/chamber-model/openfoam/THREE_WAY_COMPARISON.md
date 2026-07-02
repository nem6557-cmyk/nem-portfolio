# Three-condenser manifold comparison (read the caveats)

| config  | tube ID | inlet model (as built)            | CoV   | tube dP   | distribution |
|---------|---------|-----------------------------------|-------|-----------|--------------|
| 33-tube | 3.137   | single centred axial port (faithful) | 131%  | ~0 (25 Pa)| bullseye: 1 tube ~8x mean |
| 42-tube | 1.39    | top-fed vertical manifolds (faithful)| 10%   | ~1.4 kPa  | uniform; top-centre slightly favored |
| 66-tube | 1.6     | SIMPLIFIED centreline feed plenum    | 57%*  | ~0.6 kPa  | centred jet hits ~3-4 middle tubes |

CAVEAT: the three use DIFFERENT inlet models, so CoV is NOT a clean apples-to-apples apparatus
comparison. The 42-tube is the most directly meaningful (faithful top-fed manifold, and it is the
validated geometry). The 66 CoV is inflated by its simplified centreline-jet inlet (*see RESULTS.md);
its real lofted diffuser would distribute far better. The 33-tube bullseye is real for a single
centred port. 

Robust physics that DOES transfer: wide bores (33: ID3.137, 66: ID1.6, many parallel) make the tube
bundle hydraulically near-invisible (drop at the ports); the narrow 42 bores (ID1.39) carry a real
share. Distribution is governed by the manifold feed geometry, not tube count - the headline lesson.
