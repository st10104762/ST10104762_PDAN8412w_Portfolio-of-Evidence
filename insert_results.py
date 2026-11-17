"""
insert_results.py - copy the REAL outputs of the executed POE notebook into the Word report.

What it does
  * fills Table 8 (acceptance criteria) and Table 9 (test-set metrics) from model_comparison.csv / success_criteria.json
  * replaces the yellow placeholders for Figures 6, 7 and 8 with the PNGs the notebook saved
  * writes short, number-driven result sentences (executive summary, Section 8.2, conclusion) - review and edit them
  * removes the yellow "Results status" note

Nothing is estimated: if a results file is missing the script stops and tells you which one.

How to use
  1. Run ALL cells of the notebook (it creates poe_cnn_work/results/ and poe_cnn_work/results/figures/).
  2. pip install python-docx           (once)
  3. Put this script, the report .docx and the poe_cnn_work folder in the same folder, then run:
         python insert_results.py
     Optional: python insert_results.py --report MyReport.docx --results poe_cnn_work/results --out Final.docx
  4. Open the output in Word, press Ctrl+A then F9 (update fields) so the contents page and lists refresh, and
     read the generated sentences: they are drafts built from your numbers, so edit them into your own words.
"""
import argparse, copy, json, sys
from pathlib import Path

try:
    import pandas as pd
    from docx import Document
    from docx.shared import Inches
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError as err:
    sys.exit(f"Missing package ({err.name}). Install with:  pip install python-docx pandas")

DEFAULT_REPORT = "ST10104762_Katlego-Thejane_PDAN8412w_POE_Report.docx"

# ----------------------------------------------------------------------------------------------- loading
def load_results(res_dir: Path):
    need = ["model_comparison.csv", "success_criteria.json", "confusion_matrices.json", "recall_by_class.csv", "run_summary.json"]
    missing = [n for n in need if not (res_dir / n).exists()]
    figs = [res_dir / "figures" / n for n in ("fig6_sample_covers.png", "fig7_learning_curves.png", "fig8_confusion_matrices.png")]
    missing += [str(f.relative_to(res_dir)) for f in figs if not f.exists()]
    if missing:
        sys.exit("These notebook outputs are missing, so nothing was changed:\n  - " + "\n  - ".join(missing) +
                 f"\nRun every cell of the notebook first (looked in {res_dir.resolve()}).")
    cmp_ = pd.read_csv(res_dir / "model_comparison.csv", index_col="model")
    crit = json.loads((res_dir / "success_criteria.json").read_text())
    cms = json.loads((res_dir / "confusion_matrices.json").read_text())
    run = json.loads((res_dir / "run_summary.json").read_text())
    recall = pd.read_csv(res_dir / "recall_by_class.csv", index_col=0)
    return cmp_, crit, cms, run, recall, figs

# ----------------------------------------------------------------------------------------------- helpers
def find_table(doc, first_header, second_header):
    for t in doc.tables:
        cells = t.rows[0].cells
        if cells[0].text.strip() == first_header and cells[1].text.strip() == second_header:
            return t
    sys.exit(f"Could not find the table headed '{first_header} | {second_header}' in the report.")

def set_cell(cell, text):
    """Replace the text of a cell's first run and remove the yellow highlight."""
    run = cell.paragraphs[0].runs[0]
    run.text = text
    rpr = run._r.get_or_add_rPr()
    for h in rpr.findall(qn("w:highlight")):
        rpr.remove(h)

def para_with(doc, token):
    for p in doc.paragraphs:
        if token in p.text:
            return p
    return None

def clear_runs(p):
    for r in list(p._p):
        if r.tag != qn("w:pPr"):
            p._p.remove(r)

def write_text(p, text):
    clear_runs(p)
    p.add_run(text)

def insert_paragraph_after(p, text):
    new = copy.deepcopy(p._p)
    p._p.addnext(new)
    from docx.text.paragraph import Paragraph
    np_ = Paragraph(new, p._parent)
    write_text(np_, text)
    return np_

def put_figure(doc, token, png, width_in, alt):
    p = para_with(doc, token)
    if p is None:
        print(f"  ! placeholder {token} not found - skipped (already inserted?)"); return
    clear_runs(p)
    ppr = p._p.get_or_add_pPr()
    for child in list(ppr):                       # drop the dashed box, shading and fixed line height of the placeholder
        if child.tag in (qn("w:pBdr"), qn("w:shd"), qn("w:spacing")):
            ppr.remove(child)
    sp = OxmlElement("w:spacing"); sp.set(qn("w:after"), "40"); sp.set(qn("w:before"), "120")
    ppr.insert(1 if ppr.find(qn("w:keepNext")) is not None else 0, sp)
    run = p.add_run()
    run.add_picture(str(png), width=Inches(width_in))
    docpr = run._r.find(".//" + qn("wp:docPr"))
    docpr.set("descr", alt); docpr.set("title", alt)

# ----------------------------------------------------------------------------------------------- generated sentences
def build_text(cmp_, crit, cms, run, recall):
    b, t = cmp_.loc["Baseline CNN"], cmp_.loc["Retrained CNN"]
    n = run.get("test_n", "n/a")
    met = [crit["macro_f1_improved"], crit["accuracy_at_least_0.70"], crit["minimum_class_recall_at_least_0.60"], crit["generalisation_gap_at_most_0.10"]]
    k = sum(met)
    acc = float(t["accuracy"])
    level = "well above" if acc >= 0.50 else ("modestly above" if acc >= 0.30 else "close to")
    delta = float(t["macro_f1"] - b["macro_f1"])

    cm = cms["retrained"]; err = adj = 0
    for i, row in enumerate(cm):
        for j, v in enumerate(row):
            if i != j:
                err += v; adj += v if abs(i - j) == 1 else 0
    adj_txt = (f" Of the retrained model’s {err} test errors, {adj / err * 100:.0f}% fall between adjacent popularity tiers (Figure 8)."
               if err else " The retrained model made no test errors (Figure 8).")

    exec_ = (f"On the {n} unseen test images, the retrained CNN reached accuracy {t['accuracy']:.3f} and macro F1 {t['macro_f1']:.3f}, "
             f"against {b['accuracy']:.3f} and {b['macro_f1']:.3f} for the baseline, and met {k} of the 4 acceptance criteria (Section 8).")

    p1 = (f"On the hold-out test set (n = {n}), the baseline CNN reached accuracy {b['accuracy']:.3f} and macro F1 {b['macro_f1']:.3f}; "
          f"the retrained CNN reached {t['accuracy']:.3f} and {t['macro_f1']:.3f} (Table 9). Retraining "
          f"{'improved' if crit['macro_f1_improved'] else 'did not improve'} macro F1 ({delta:+.3f}). With four balanced classes, chance accuracy is 0.25, "
          f"so the retrained accuracy is {level} chance level.")
    p2 = (f"At its best epoch ({crit['best_epoch']}), the retrained model’s train–validation accuracy gap was {crit['generalisation_gap']:.3f} "
          f"(baseline: {crit['baseline_gap']:.3f} at epoch {crit['baseline_best_epoch']}), "
          f"{'within' if crit['generalisation_gap_at_most_0.10'] else 'outside'} the 0.10 limit (Figure 7); because training accuracy is measured with "
          f"augmentation and dropout active, a small gap is expected. Its weakest class was {crit['weakest_class']} (recall {crit['minimum_class_recall']:.3f})."
          + adj_txt)
    verdict = "accepted" if crit["accepted"] else "not accepted"
    p3 = (f"The retrained model met {k} of 4 acceptance criteria (Table 8) and is therefore {verdict}"
          + ("." if crit["accepted"] else (", and the baseline remains the preferred model." if not crit["macro_f1_improved"] else "."))
          + (" Performance near chance supports the Section 9 caveat that cover artwork carries little reliable signal of reader popularity." if level == "close to" else ""))
    concl = (f"Against the Section 8 criteria, the retrained CNN met {k} of 4 and is therefore "
             f"{'accepted' if crit['accepted'] else 'not accepted for deployment'}.")
    return exec_, [p1, p2, p3], concl, met

# ----------------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", default=DEFAULT_REPORT)
    ap.add_argument("--results", default="poe_cnn_work/results")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    report, res_dir = Path(a.report), Path(a.results)
    if not report.exists():
        sys.exit(f"Report not found: {report.resolve()}")
    out = Path(a.out) if a.out else report.with_name(report.stem + "_FINAL.docx")

    cmp_, crit, cms, run, recall, figs = load_results(res_dir)
    doc = Document(str(report))
    b, t = cmp_.loc["Baseline CNN"], cmp_.loc["Retrained CNN"]

    # Table 9: metrics
    t9 = find_table(doc, "Metric", "Baseline CNN")
    metric_cols = ["accuracy", "macro_precision", "macro_recall", "macro_f1", "weighted_precision", "weighted_recall", "weighted_f1"]
    for row, col in zip(t9.rows[1:], metric_cols):
        set_cell(row.cells[1], f"{b[col]:.3f}"); set_cell(row.cells[2], f"{t[col]:.3f}")

    # Table 8: acceptance criteria
    t8 = find_table(doc, "Criterion", "Threshold")
    exec_, narrative, concl, met = build_text(cmp_, crit, cms, run, recall)
    observed = [f"{t['macro_f1']:.3f} vs {b['macro_f1']:.3f}", f"{t['accuracy']:.3f}",
                f"{crit['minimum_class_recall']:.3f} ({crit['weakest_class']})", f"{crit['generalisation_gap']:.3f} (epoch {crit['best_epoch']})"]
    for row, ok, obs in zip(t8.rows[1:], met, observed):
        set_cell(row.cells[2], f"{'Met' if ok else 'Not met'}: {obs}")

    # Figures 6-8
    put_figure(doc, "{{FIG6}}", figs[0], 4.0, "Random sample of six validated cover images from each of the four popularity tiers.")
    put_figure(doc, "{{FIG7}}", figs[1], 4.6, "Training and validation accuracy and loss by epoch for the baseline and retrained CNNs.")
    put_figure(doc, "{{FIG8}}", figs[2], 5.4, "Test-set confusion matrices for the baseline and retrained CNNs.")

    # Generated sentences
    for token, text in (("{{EXEC_RESULT}}", exec_), ("{{CONCLUSION_RESULT}}", concl)):
        p = para_with(doc, token)
        if p is not None: write_text(p, text)
    p = para_with(doc, "{{RESULTS_NARRATIVE}}")
    if p is not None:
        write_text(p, narrative[0])
        last = p
        for text in narrative[1:]:
            last = insert_paragraph_after(last, text)
    note = para_with(doc, "{{RESULTS_NOTE}}")
    if note is not None:
        note._p.getparent().remove(note._p)

    doc.save(str(out))
    print(f"Saved: {out.resolve()}")
    print(f"Criteria met: {sum(met)} of 4 | retrained accepted: {crit['accepted']}")
    print("Next: open in Word, press Ctrl+A then F9 to refresh the contents page and lists, and edit the generated sentences.")

if __name__ == "__main__":
    main()
