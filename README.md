# Dealing the House's Edge: Nevada blackjack take, 2000-2026

DSAN 5100 Group 6 (Mike, Jason, Norman, Zichen). See `docs/proposal/Group 6.pdf` and `CLAUDE.md`.

## Setup
```
uv sync
uv run pytest
```

## Data provenance
| Dataset | Status | Location |
|---|---|---|
| NGCB Gaming Revenue (combined Game & Table, by area, 1983-) | present; **not blackjack-only** | `data/raw/` |
| NGCB blackjack-only | request to NGCB pending | missing |
| Casino ownership / HHI | to be built | missing |
| LVCVA visitor volume | to be downloaded | missing |
| FRED Nevada unemployment | to be downloaded | missing |

## Layout
`data/{raw,interim,processed,external}`, `src/blackjack_take/{data,stats,ts}`, `tests/`, `notebooks/`, `reports/{figures,tables}`, `docs/`.
