"""Generate a portable, mobile-readable HTML report from actual run metrics."""

import argparse
import html
import json
from pathlib import Path


def render(metrics, output):
    rows = [json.loads(line) for line in Path(metrics).read_text().splitlines() if line.strip()]
    if not rows:
        raise ValueError("No recorded metrics")
    columns = [
        "epoch",
        "loss",
        "validation_accuracy",
        "teacher_validation_accuracy",
        "samples_per_second",
        "peak_rank_vram_bytes",
        "updates",
    ]
    body = "".join(
        "<tr>"
        + "".join("<td>" + html.escape(str(row.get(k, "unavailable"))) + "</td>" for k in columns)
        + "</tr>"
        for row in rows
    )
    headers = "".join("<th>" + k.replace("_", " ") + "</th>" for k in columns)
    document = (
        """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Lifelong Catch and Correct | Distillation</title><style>
body{font:16px system-ui;background:#101827;color:#edf2fa;margin:0;padding:24px;line-height:1.6}
main{max-width:1200px;margin:auto}h1{font-size:clamp(24px,5vw,40px)}
section,aside{background:#19263a;padding:20px;border-radius:12px;margin:20px 0}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #42516a}
th{color:#afd4ff}aside{border-left:4px solid #75acff}code{overflow-wrap:anywhere}
</style><main><h1>Lifelong Catch and Correct</h1><p>Recorded distillation run metrics</p>
<section class="scroll"><table><thead><tr>"""
        + headers
        + "</tr></thead><tbody>"
        + body
        + """</tbody></table></section>
<aside><h2>Review guidance</h2><p>This is an offline results viewer, not an AI assistant or a training controller.
Compare held-out accuracy before accepting speed improvements. Throughput includes training data loading,
compute and gradient communication; it excludes validation, checkpoint writes and initial checksum validation.
The first epoch can include compiler warmup. CPU runs report zero GPU memory.</p>
<p>Changes require a regression test and a new measured run. No automatic code mutation or external API calls occur.</p></aside></main></html>"""
    )
    Path(output).write_text(document)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics")
    parser.add_argument("output")
    args = parser.parse_args()
    render(args.metrics, args.output)
