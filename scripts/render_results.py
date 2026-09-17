"""Build accessible research figures directly from saved SQL aggregate counts."""
import argparse
import csv
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAVY, TEAL, GRAY = "#142d42", "#087e83", "#687b89"


def rows(name):
    with (ROOT / "outputs" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def text(x, y, value, size=16, color=NAVY, anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'


def start(title, subtitle, height, desc):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}" role="img" aria-labelledby="title desc">',
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
            '<rect width="100%" height="100%" fill="white"/><g font-family="Arial, sans-serif">',
            text(40, 48, title, 29), text(40, 82, subtitle, 16, GRAY)]


def finish(parts):
    return "\n".join(parts + ['</g></svg>']) + "\n"


def build_outputs():
    cohort = rows("04_cohort_retention.csv")
    keys = [(r["cohort_month"], int(r["month_number"])) for r in cohort]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate cohort-month cells.")
    cohorts = sorted({r["cohort_month"] for r in cohort})
    parts = start("Activity across signup cohorts", "Synthetic 2025 cohort data | each cell: active members / original signups", 665,
                  "Calendar-month activity heatmap. Each cell labels its numerator and original-cohort denominator. Returning members can reappear; this is not a survival curve.")
    for month in range(7):
        parts.append(text(257 + 116 * month, 139, f"Month {month}", 16, GRAY, "middle"))
    for i, name in enumerate(cohorts):
        y = 168 + i * 62
        parts.append(text(40, y + 29, name[:7], 18))
        for month in range(7):
            found = [r for r in cohort if r["cohort_month"] == name and int(r["month_number"]) == month]
            if not found:
                parts.append(text(257 + month * 116, y + 30, "Not observed", 13, GRAY, "middle"))
                continue
            r = found[0]
            numerator, denominator = int(r["active_members"]), int(r["cohort_size"])
            if not 0 <= numerator <= denominator or denominator <= 0:
                raise ValueError("Invalid cohort denominator or count.")
            rate = numerator / denominator
            # Fixed 0-100% light-to-dark scale, shared across all cells.
            rgb = tuple(round(a + rate * (b - a)) for a, b in zip((235, 245, 245), (8, 100, 105)))
            fill = '#%02x%02x%02x' % rgb
            x = 203 + month * 116
            parts.append(f'<rect x="{x}" y="{y}" width="108" height="54" rx="4" fill="{fill}"/>')
            linear = [v / 255 / 12.92 if v / 255 <= .04045 else ((v / 255 + .055) / 1.055) ** 2.4 for v in rgb]
            luminance = sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
            ink = "white" if 1.05 / (luminance + .05) >= (luminance + .05) / .05 else "#000000"
            parts += [text(x + 54, y + 22, f"{rate:.0%}", 18, ink, "middle"),
                      text(x + 54, y + 42, f"{numerator}/{denominator}", 13, ink, "middle")]
    parts += [text(40, 579, "Darker cells indicate a higher fraction active (common 0–100% scale).", 15, GRAY),
              text(40, 610, "Month 0 is the signup calendar month; exposure days vary. Activity can resume after an inactive month.", 15, GRAY),
              text(40, 639, "Source: 04_cohort_retention.sql. Frozen synthetic example through December 2025; not causal evidence.", 14, GRAY)]
    heatmap = finish(parts)
    funnel = rows("03_activation_funnel.csv")
    summaries = []
    for channel in sorted({r["acquisition_channel"] for r in funnel}):
        chosen = [r for r in funnel if r["acquisition_channel"] == channel]
        n, active, retained = [sum(int(r[k]) for r in chosen) for k in ("signups", "activated_members", "retained_members")]
        if not 0 <= retained <= active <= n or n <= 0:
            raise ValueError("Funnel counts must be nested and have positive denominators.")
        summaries.append((channel, n, active, retained))
    parts = start("Activation and continued use", "Synthetic January–June 2025 signups | all rates use original signups as the denominator", 555,
                  "Paired activation within 14 days and continued-use by 45-day rates, with exact counts by acquisition channel. Continued use requires activity in both windows.")
    left, right = 225, 700
    for tick in range(0, 101, 20):
        x = left + (right - left) * tick / 100
        parts += [f'<line x1="{x}" y1="156" x2="{x}" y2="397" stroke="#dae3e9"/>', text(x, 424, f"{tick}%", 14, GRAY, "middle")]
    parts += [text(765, 135, "Activated / signups", 14, GRAY), text(930, 135, "Retained / signups", 14, GRAY)]
    for i, (channel, n, active, retained) in enumerate(summaries):
        y = 186 + i * 62
        xa, xr = left + (right - left) * active / n, left + (right - left) * retained / n
        parts += [text(40, y, channel, 18), text(40, y + 21, f"n = {n}", 14, GRAY),
                  f'<line x1="{xr}" y1="{y}" x2="{xa}" y2="{y}" stroke="{GRAY}" stroke-width="2"/>',
                  f'<circle cx="{xa}" cy="{y}" r="6" fill="white" stroke="{GRAY}" stroke-width="2"/>',
                  f'<circle cx="{xr}" cy="{y}" r="6" fill="{TEAL}"/>',
                  text(765, y + 5, f"{active}/{n} ({active/n:.1%})", 15),
                  text(930, y + 5, f"{retained}/{n} ({retained/n:.1%})", 15)]
    totals = [sum(row[k] for row in summaries) for k in (1, 2, 3)]
    parts += [text(225, 465, "Open: activated within 14 days   |   Filled: activity in both 0–14 and 15–45 days", 15, GRAY),
              text(40, 505, f"Overall: {totals[0]} signups → {totals[1]} activated → {totals[2]} retained. Rates are pooled from counts, not averaged.", 15, GRAY),
              text(40, 534, "Source: 03_activation_funnel.sql. Descriptive synthetic comparisons; no channel effect is identified.", 14, GRAY)]
    report = "\n\n".join([
        "# Executed SQL analysis report", "## Question and data",
        "Which acquisition channels activate and retain members, and how does calendar-month activity differ across cohorts? The normalized SQLite case study contains 480 deterministic synthetic members across eight sites. The analysis window is frozen to 2025; a production extension must parameterize dates and censor incomplete follow-up windows.",
        "## Activation and continued use", "![Channel activation and continued use with exact denominators](../assets/activation-retention.svg)",
        "Activation requires a completed event from signup through day 14. Retention requires both activation and a completed event during days 15–45. Both rates divide by all original signups, not by the activated subset. Aggregate rates pool counts across months.",
        "## Calendar-month activity", "![Cohort activity heatmap with cell counts](../assets/cohort-retention.svg)",
        "Monthly activity counts any completed service in the calendar month. Returning members can reappear, so this is not monotone survival retention. Month zero has unequal exposure time depending on signup day. The explicit denominator remains the original cohort, including inactive members.",
        "## Checks, interpretation, and reproduction",
        "Foreign keys, database grain, zero-failure QA queries, bounded rates, and the deliberately constructed Summit anomaly are integration-tested. Figure checks validate nested funnel counts and unique cohort cells; CI verifies that regenerated figures and this report match committed files.",
        "The [decision memo](../docs/decision-memo.md) discusses support experience and operational review. These descriptive synthetic patterns do not establish channel or support-speed effects. Counts are complete for the constructed fixture; no population sampling confidence intervals are implied.",
        "Run `python scripts/build_demo_database.py`, `python scripts/run_queries.py`, `python scripts/render_results.py`, and `python -m unittest discover -s tests -v`. No third-party Python packages are required. [Funnel data](03_activation_funnel.csv) · [Cohort data](04_cohort_retention.csv) · [Metric definitions](../docs/metric-definitions.md).",
    ]) + "\n"
    return {"assets/cohort-retention.svg": heatmap, "assets/activation-retention.svg": finish(parts), "outputs/report.md": report}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in build_outputs().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale generated result: {name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
