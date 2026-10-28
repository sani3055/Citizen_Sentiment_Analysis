import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r"D:\CITY PRJ")
TEMPLATE = Path(r"D:\Downloads\Journal_Manuscript_Template with Formatting Instructions.docx")
OUT = ROOT / "outputs" / "Citizen_Sentiment_Analysis_Journal_Manuscript_Second_Level_Corrected.docx"
FIG = ROOT / "reports" / "figures"


def load_json(name):
    with (ROOT / "reports" / "metrics" / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_width(cell, width_inches):
    cell.width = Inches(width_inches)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def set_run_font(run, size=11, bold=None, italic=None, color=None):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def set_no_proofing(paragraph):
    """Disable spell-check markup for mathematical notation in a paragraph."""
    for run in paragraph.runs:
        r_pr = run._element.get_or_add_rPr()
        no_proof = r_pr.find(qn("w:noProof"))
        if no_proof is None:
            r_pr.append(OxmlElement("w:noProof"))


def format_math_notation(paragraph):
    """Apply real Word subscript/superscript formatting to common notation.

    The manuscript is authored as readable text, but tokens such as x_c and
    R2 should render as mathematical notation in Word rather than as literal
    underscores or baseline digits.  Only unambiguous short tokens are
    transformed, so dataset field names such as resolution_description are
    left untouched.
    """
    if len(paragraph.runs) != 1:
        return
    source = paragraph.runs[0]
    text = source.text or ""
    pattern = re.compile(r"(?<![A-Za-z])([xyzdrfεC])_([A-Za-z0-9]+)|R-squared|R2|C_v")
    if not pattern.search(text):
        return

    base_rpr = deepcopy(source._r.rPr) if source._r.rPr is not None else None
    paragraph._p.remove(source._r)

    def add_part(value, script=None):
        if not value:
            return
        run = paragraph.add_run(value)
        if base_rpr is not None:
            run._r.insert(0, deepcopy(base_rpr))
        if script == "sub":
            run.font.subscript = True
        elif script == "sup":
            run.font.superscript = True
        r_pr = run._element.get_or_add_rPr()
        if r_pr.find(qn("w:noProof")) is None:
            r_pr.append(OxmlElement("w:noProof"))

    cursor = 0
    for match in pattern.finditer(text):
        add_part(text[cursor:match.start()])
        token = match.group(0)
        if match.group(1):
            add_part(match.group(1))
            add_part(match.group(2), "sub")
        elif token == "C_v":
            add_part("C")
            add_part("v", "sub")
        elif token == "R-squared":
            add_part("R")
            add_part("2", "sup")
        else:  # R2
            add_part("R")
            add_part("2", "sup")
        cursor = match.end()
    add_part(text[cursor:])


def set_para(p, before=0, after=6, line=1.08, align=None, keep=False):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if align is not None:
        p.alignment = align
    if keep:
        p._p.get_or_add_pPr().append(OxmlElement("w:keepNext"))


def add_text(doc, text, style="Normal", size=11, bold=False, italic=False, align=None, before=0, after=6, line=1.08):
    p = doc.add_paragraph(style=style)
    set_para(p, before, after, line, align)
    r = p.add_run(text)
    set_run_font(r, size, bold, italic)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    set_para(p, before=10 if level == 1 else 7, after=4, line=1.0, keep=True)
    r = p.add_run(text)
    set_run_font(r, 13 if level == 1 else 11.5, True)
    return p


def add_numbered(doc, text):
    try:
        p = doc.add_paragraph(style="List Number")
    except KeyError:
        p = doc.add_paragraph(style="List Paragraph")
    set_para(p, after=4, line=1.05)
    r = p.add_run(text)
    set_run_font(r, 11)
    return p


def add_caption(doc, text, above=False):
    p = doc.add_paragraph()
    set_para(p, before=4 if above else 2, after=4, line=1.0)
    r = p.add_run(text)
    set_run_font(r, 9.5, bold=True)
    return p


def add_figure(doc, filename, caption, width=6.1):
    path = FIG / filename
    if not path.exists():
        add_text(doc, f"[Figure unavailable: {filename}]", size=10, italic=True)
        return
    p = doc.add_paragraph()
    set_para(p, before=4, after=2, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    inline_shape = p.add_run().add_picture(str(path), width=Inches(width))
    # Provide descriptive metadata for screen readers and document audits.
    doc_pr = inline_shape._inline.docPr
    doc_pr.set("descr", caption)
    doc_pr.set("title", filename)
    add_caption(doc, caption, above=False)


def add_table(doc, headers, rows, widths, caption):
    add_caption(doc, caption, above=True)
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    # The supplied journal template does not define Word's built-in
    # ``Table Grid`` style, so apply a compact border directly.
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "B7C9D6")
        borders.append(border)
    tbl_pr.append(borders)
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        set_cell_width(cell, widths[j])
        set_cell_shading(cell, "D9EAF2")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        set_para(p, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
        r = p.add_run(h)
        set_run_font(r, 8.5, True)
    # Mark the first row as a repeating/header row for accessibility and
    # multi-page table rendering.
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)
    for row in rows:
        cells = table.add_row().cells
        for j, value in enumerate(row):
            set_cell_width(cells[j], widths[j])
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cells[j].paragraphs[0]
            set_para(p, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT)
            r = p.add_run(str(value))
            set_run_font(r, 8.2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_reference(doc, text):
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    set_para(p, after=3, line=1.0)
    r = p.add_run(text)
    set_run_font(r, 9.5)


def clear_body(doc):
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def main():
    vader = load_json("vader_metrics.json")
    topics = load_json("topic_coherence.json")
    absa = load_json("absa_metrics.json")
    transformer = load_json("transformer_metrics.json")
    outcomes = load_json("outcomes_summary.json")
    repeat_sensitivity = load_json("repeat_rate_sensitivity.json")
    integration = load_json("integration_summary.json")
    predictive = load_json("lagged_predictive_modeling_results.json")
    robustness = load_json("robustness_results.json")
    ranking = load_json("priority_ranking_metrics.json")
    review = load_json("review_corrections_results.json")
    nyc_count = len(pd.read_parquet(ROOT / "data" / "raw" / "nyc311_raw.parquet", columns=["unique_key"]))
    rsat_count = len(pd.read_parquet(ROOT / "data" / "raw" / "rsat_raw.parquet", columns=["unique_key"]))
    delay_models = predictive["results_by_target"]["mean_resolution_delay_hours"]
    repeat_models = predictive["results_by_target"]["repeat_request_rate_14d"]
    # LightGBM is the single primary recipe used for the headline comparison,
    # robustness analysis, SHAP interpretation, and dashboard evidence. Ridge
    # and RandomForest remain transparent comparison models in Table 4.
    primary_algorithm = review["primary_algorithm"]
    delay_selected = primary_algorithm
    repeat_selected = primary_algorithm
    delay_result = delay_models["algorithms"][delay_selected]
    repeat_result = repeat_models["algorithms"][repeat_selected]
    split_counts = predictive["split_counts"]
    absa_rule = absa["models"]["rule_based_baseline"]
    absa_tfidf = absa["models"]["tfidf_logistic_regression"]
    transformer_test = transformer["evaluation_metrics_out_of_time"]

    def best_model(target_results, feature_set):
        return max(
            target_results["algorithms"].items(),
            key=lambda item: item[1][feature_set]["test_metrics"]["r2"],
        )

    delay_best_base_name, delay_best_base = best_model(delay_models, "baseline")
    delay_best_aug_name, delay_best_aug = best_model(delay_models, "augmented")
    repeat_best_base_name, repeat_best_base = best_model(repeat_models, "baseline")
    repeat_best_aug_name, repeat_best_aug = best_model(repeat_models, "augmented")
    delay_best_gap = delay_best_aug["augmented"]["test_metrics"]["r2"] - delay_best_base["baseline"]["test_metrics"]["r2"]
    repeat_best_gap = repeat_best_aug["augmented"]["test_metrics"]["r2"] - repeat_best_base["baseline"]["test_metrics"]["r2"]
    delay_overall_verb = "exceeded" if delay_best_gap > 0 else "did not exceed"
    repeat_overall_verb = "exceeded" if repeat_best_gap > 0 else "did not exceed"
    predictive_rows = []
    for target_label, target_results in [
        ("Mean delay (hours)", delay_models),
        ("Repeat rate (14d)", repeat_models),
    ]:
        for algorithm, result in target_results["algorithms"].items():
            predictive_rows.append([
                target_label,
                algorithm,
                f"{result['baseline']['test_metrics']['r2']:.4f}",
                f"{result['augmented']['test_metrics']['r2']:.4f}",
                f"{result['delta_r2']:+.4f}",
                f"{result['paired_ttest_p_value']:.4g}",
            ])
    delay_robust = robustness["results_by_target"]["mean_resolution_delay_hours"]
    repeat_robust = robustness["results_by_target"]["repeat_request_rate_14d"]

    doc = Document(str(TEMPLATE))
    clear_body(doc)
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Replace the template's review placeholder in the running header.
    header = section.header
    hp = header.paragraphs[0]
    hp.text = "Citizen Sentiment Analysis of Municipal Services"
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in hp.runs:
        set_run_font(run, 8.5, italic=True, color="666666")

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(11)

    # Title and author block.
    add_text(doc, "Do Language and Satisfaction Signals Improve One-Month-Ahead Prediction of Municipal Service Delays and Repeat Requests? Evidence from NYC 311", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    author_p = doc.add_paragraph()
    set_para(author_p, after=3, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    for text, script in [
        ("Taher Panbiharwala", None), ("1", "sup"), (", ", None),
        ("Sanidhya Bhandari", None), ("1", "sup"), (", ", None),
        ("*", "sup"), (", ", None), ("Chinmoy Deb", None), ("1", "sup"),
    ]:
        run = author_p.add_run(text)
        set_run_font(run, 11)
        if script == "sup":
            run.font.superscript = True

    affiliation_p = doc.add_paragraph()
    set_para(affiliation_p, after=2, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    affiliation_marker = affiliation_p.add_run("1")
    set_run_font(affiliation_marker, 9.5, italic=True)
    affiliation_marker.font.superscript = True
    affiliation_text = affiliation_p.add_run(" School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, Vellore, Tamil Nadu 632014, India")
    set_run_font(affiliation_text, 9.5, italic=True)

    corresponding_p = doc.add_paragraph()
    set_para(corresponding_p, after=9, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER)
    corresponding_marker = corresponding_p.add_run("*")
    set_run_font(corresponding_marker, 9.5, italic=True)
    corresponding_marker.font.superscript = True
    corresponding_text = corresponding_p.add_run(" Corresponding author: Sanidhya Bhandari, sanidhya.bhandari2023@vitstudent.ac.in")
    set_run_font(corresponding_text, 9.5, italic=True)
    set_no_proofing(author_p)
    set_no_proofing(affiliation_p)
    set_no_proofing(corresponding_p)

    add_heading(doc, "Abstract", 1)
    add_text(doc, f"A municipal 311 record shows what was reported and when an agency closed the request, but closure does not necessarily mean that the resident was satisfied or that the underlying condition ended. This paper tests whether sentiment, topic, grievance-aspect, and survey features improve one-month-ahead prediction of resolution delay and repeat requests. We combine {nyc_count:,} NYC 311 service requests with {rsat_count:,} Resolution Satisfaction Survey responses at a privacy-safe service-borough-year-month grain. Topic models are fitted on training-period text only, all operational features are lagged by one month, and duplicate agency boilerplate is controlled within the ABSA split. On {split_counts.get('test', 0):,} held-out 2024 cells, the primary LightGBM delay model changed R-squared from {delay_result['baseline']['test_metrics']['r2']:.4f} to {delay_result['augmented']['test_metrics']['r2']:.4f} (Delta R-squared = {delay_result['delta_r2']:+.4f}; augmented performance was worse, paired absolute-error p = {delay_result['paired_ttest_p_value']:.4g}). For repeat rate, the primary model changed R-squared from {repeat_result['baseline']['test_metrics']['r2']:.4f} to {repeat_result['augmented']['test_metrics']['r2']:.4f} (Delta R-squared = {repeat_result['delta_r2']:+.4f}; the augmented model was slightly better, paired absolute-error p = {repeat_result['paired_ttest_p_value']:.4g}). However, simple last-value baselines reached R-squared {review['naive_baselines']['mean_resolution_delay_hours']['last_value']['r2']:.3f} for delay and {review['naive_baselines']['repeat_request_rate_14d']['last_value']['r2']:.3f} for repeat rate. The result is therefore a useful negative or near-null finding: language and satisfaction signals do not consistently improve the strongest temporal benchmark. Held-out Precision@k evaluates the dashboard queue, while agency-authored text, one-city coverage, and address-based repeat proxies limit generalisation.", size=10.5, after=7, line=1.05)
    add_text(doc, "Keywords: municipal services; citizen satisfaction; sentiment analysis; aspect-based sentiment analysis; transformer NLP; NYC 311", size=10.5, bold=True, after=8)

    add_heading(doc, "1. Introduction", 1)
    add_text(doc, """Cities use 311 systems to collect requests about services such as sanitation, housing, noise, parking, and infrastructure. These records are useful because they include time, location, service type, and closure information. Still, a ticket marked closed is an administrative outcome; it is not proof that the resident felt the issue was resolved. Earlier studies also show that 311 activity is influenced by neighbourhood conditions, reporting behaviour, and the visibility of particular services [1-4].

    Text features can add context that is missing from counts and timestamps. VADER gives a simple and transparent sentiment baseline [5]. Transformer models are more flexible with context, while LDA and BERTopic help group recurring themes [6-8]. ABSA is useful for municipal feedback because dissatisfaction can concern response time, issue correction, communication, or work quality rather than one general sentiment label. At the same time, public-sector text is different from product reviews, and a model trained in another domain may not transfer well [9-12].

    The main question in this work is practical: after accounting for service, borough, season, and request volume, do language and satisfaction signals improve prediction of municipal outcomes? Civic NLP papers often stop at sentiment or topic description, while operational 311 models often use structured variables alone. Few studies put both types of evidence into the same model and then test it on a later time period. There is also an important privacy boundary here. The public RSAT data do not provide unrestricted citizen comments, so this paper uses survey satisfaction and standardised dissatisfaction reasons as aggregate evidence. The text features come from official 311 resolution descriptions.

    We therefore test whether adding these features improves out-of-time prediction of mean resolution delay and 14-day repeat-request rate. The results are predictive associations, not evidence of a causal effect.""")
    add_text(doc, "The study makes four practical contributions:")
    add_numbered(doc, "A privacy-safe multi-source integration design that joins NYC 311 operations and RSAT survey evidence at service-borough-year-month grain without claiming a request-level match.")
    add_numbered(doc, "A reproducible NLP pipeline that compares lexicon sentiment, topic discovery, supervised ABSA, and Transformer adaptation under chronological evaluation.")
    add_numbered(doc, "A service-controlled, one-month-ahead comparison that reports algorithm-specific gains, the strongest structured benchmark, paired absolute-error tests, and bootstrap uncertainty.")
    add_numbered(doc, "An operational dashboard that exposes priority cells, historical trends, and model evidence for municipal and resident-facing use.")
    add_text(doc, "The remainder of this paper is organised as follows. Section 2 reviews related work. Section 3 describes the data, formulation, NLP pipeline, outcomes, experimental design, and reproducibility controls. Section 4 reports descriptive, NLP, predictive, robustness, and explainability results. Section 5 discusses interpretation, practical implications, and limitations. Section 6 concludes.")

    add_heading(doc, "2. Literature Review", 1)
    add_heading(doc, "2.1 Sentiment analysis and Transformer models", 2)
    add_text(doc, """Lexicon methods are still useful when labelled examples are limited. They are quick to run, easy to inspect, and provide a baseline that other models should beat. VADER was designed for short, informal text and uses lexical, grammatical, and punctuation cues [5]. Its limitation in this project is vocabulary: a formal closure description may contain words that look positive or negative without expressing a resident's actual experience. This is part of the wider trade-off between simple, transparent methods and domain adaptation [13, 14].

    Transformer pretraining made it possible to use context more effectively in text classification. BERT introduced bidirectional representations that can be fine-tuned for a specific task [6]. However, a larger model does not remove problems caused by noisy labels, boilerplate, local abbreviations, or implicit dissatisfaction. We use VADER as a transparent baseline and DistilBERT as a compact adapted model, while keeping the evaluation design more important than the model name.""")
    add_heading(doc, "2.2 ABSA and topic discovery in public-sector text", 2)
    add_text(doc, """ABSA links a text span or record to an aspect and its associated sentiment or grievance category. Recent surveys show a move from hand-built rules toward unified and generative models, but they also identify recurring problems: implicit aspects, domain shift, imbalanced classes, and limited annotated data [9-12]. These issues are especially relevant to public services because a record may describe the original event, the response process, or a communication failure.

    Topic models give a second view of the same text. LDA represents each document as a mixture of topics and is still useful when interpretability matters [7]. BERTopic uses sentence embeddings, clustering, and class-based TF-IDF to find groups of semantically related documents [8]. Civic studies have used these tools for government inquiries, environmental complaints, emergency management, and policing, but many of them remain descriptive [15-19]. In this project, the topic proportions and topic entropy are turned into cell-level features and tested for their value in outcome prediction.""")
    add_heading(doc, "2.3 311 data, reporting bias, and service outcomes", 2)
    add_text(doc, """Earlier 311 research shows that service-request categories contain information about urban location and neighbourhood conditions [1]. Other studies have used 311 as a social-sensing source for distress and public-health risk [2]. Work on reporting bias is important because a low complaint count does not always mean that a community has fewer problems [3, 4]. Resolution-time prediction has also been studied in helpdesk data, where ensemble models can perform well, although a corporate ticket is not the same as a municipal request [20].

    Taken together, these studies leave a useful gap. Structured 311 models often do not include language or satisfaction signals, while civic NLP studies often stop after describing sentiment or topics. This project compares both feature sets on the same service-borough-month cells, keeps a later period untouched for testing, and reports uncertainty instead of presenting only the best score.""")
    add_heading(doc, "2.4 Research gap", 2)
    add_text(doc, "The project focuses on four gaps: limited testing of civic language against operational outcomes; the separation between ABSA and municipal prediction; weak integration of service, place, and time; and unclear privacy and domain-transfer boundaries. Table 1 summarises how the present study differs from representative earlier work. The aim is not to claim that NLP solves municipal management. It is to test, under a controlled design, whether citizen-experience proxies add predictive information.")
    add_table(doc, ["Study / stream", "Approach", "Setting", "Limitation addressed here"], [
        ["Wang et al. [1]", "Structured 311 signatures", "NYC 311 / urban location", "No text or satisfaction outcome"],
        ["Kontokosta and Hong [3]", "Reporting-bias analysis", "Kansas City 311", "Does not test language augmentation"],
        ["Tang et al. [15]", "BERTopic civic inquiries", "Chinese government platform", "Descriptive; no operational target"],
        ["Tai et al. [20]", "ML resolution-time prediction", "Corporate helpdesk", "Not municipal and no citizen signal"],
        ["This study", "NLP-augmented outcome models", "NYC 311 + RSAT", "Privacy-safe aggregate, time-held-out comparison"],
    ], [1.35, 1.55, 1.65, 2.0], "Table 1. Representative related work and the gap addressed by this study.")

    add_heading(doc, "3. Methodology", 1)
    add_heading(doc, "3.1 Problem formulation", 2)
    p = add_text(doc, "The unit of analysis is a cell c = (s, b, y, m), where s denotes the service category, b the borough, y the year, and m the month. Each cell contains operational variables x_c, language features z_c, and the outcome vector y_c. The two primary outcomes are mean resolution delay d_c in hours and the 14-day repeat-request rate r_c.")
    set_no_proofing(p)
    p = add_text(doc, "y_c = f_0(x_c) + ε_c    (1)", size=11, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=3)
    set_no_proofing(p)
    p = add_text(doc, "y_c = f_1(x_c, z_c) + ε_c    (2)", size=11, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=5)
    set_no_proofing(p)
    p = add_text(doc, "The baseline model f_0 uses service identity, borough, request volume, and month-related variables. The augmented model f_1 adds VADER, topic, ABSA, and satisfaction features. We measure the change in held-out R-squared as Delta R-squared = R-squared_augmented - R-squared_baseline. A positive value means that the augmented model predicted the test cells better; it does not show that the added features caused the outcome.")
    set_no_proofing(p)

    add_heading(doc, "3.2 Data and materials", 2)
    add_text(doc, f"The first source is the NYC 311 Service Requests dataset (Socrata identifier erm2-nwe9). The case-normalised, paged extract contains {nyc_count:,} valid closed requests from January 2023 through December 2024 for the twenty selected service categories and five mapped boroughs. Every calendar month is present. Relevant fields include complaint type, borough, created and closed timestamps, location fields used for repeat detection, and resolution_description text.")
    add_text(doc, f"The second source is the NYC 311 Resolution Satisfaction Survey (RSAT; Socrata identifier 5ijn-vbdv). After study-period, borough, and Likert-value checks, {rsat_count:,} survey responses remained in the analytic sample.")
    add_table(doc, ["RSAT count", "Meaning", "Use in this study"], [
        ["Portal headline", "All records shown by the public portal", "Not used as the analytic sample"],
        [f"{rsat_count:,}", "Validated study-period responses with usable Likert values", "Used for aggregate satisfaction and standardised grievance features"],
    ], [1.15, 2.85, 2.35], "Table 3. RSAT headline count versus the audited analytic count. The difference is caused by study-window and validation filters.")
    add_text(doc, "During the schema check, we also found that the public RSAT data do not contain unrestricted citizen comments. The open-text field is not treated as citizen prose. RSAT contributes overall satisfaction and standardised dissatisfaction reasons, while the language features are extracted from official 311 resolution descriptions. This distinction matters when interpreting ABSA performance.")

    add_text(doc, "Both sources are public administrative or survey data. The integrated file contains no direct personal identifiers and the modelling is carried out at the aggregate cell level. We do not make individual predictions and do not claim a one-to-one survey-to-ticket match. Since the data are public and de-identified, the project did not involve new human intervention; a formal submission should still follow the university's ethics and data-governance requirements.")
    add_text(doc, f"At the cell level, {integration['initial_outcome_cells']:,} operational outcome cells were available, {integration['cells_matched_with_rsat']:,} matched an RSAT cell, and {integration['robust_cells_before_temporal_split']:,} met the minimum operational request threshold before temporal exclusions. VADER has a different count ({vader['number_of_matched_cells']:,}) because its benchmark requires at least ten RSAT responses in addition to a matched VADER cell. The one-month lag then requires a consecutive service-borough month pair, leaving {predictive['lagged_cells']:,} modelled cells. These filters explain the cell counts rather than representing contradictory datasets.")
    add_text(doc, "The primary operational analysis is a one-month-ahead aggregate forecast. Language, survey, volume, service, borough, and seasonal features observed in month t predict delay and repeat outcomes for the same service and borough in month t+1. The lagged target outcome is never included as a predictor; only the previous month's observed feature values are used. The original same-month model is retained only as a secondary monitoring analysis and is not presented as a pre-closure ticket forecast.")
    add_table(doc, ["Feature family", "Variables used in the primary LightGBM comparison"], [
        ["Structured", ", ".join(review["feature_groups"]["structured"])],
        ["VADER", ", ".join(review["feature_groups"]["VADER"])],
        ["Topics", ", ".join(review["feature_groups"]["topics"])],
        ["ABSA", ", ".join(review["feature_groups"]["ABSA"])],
        ["RSAT satisfaction", ", ".join(review["feature_groups"]["RSAT satisfaction"])],
    ], [1.35, 5.0], "Table 2. Explicit feature inventory. All predictors are observed at month t; target outcomes at month t+1 are excluded from the feature matrix.")
    add_figure(doc, "cell_coverage_heatmap.png", "Figure 1. RSAT survey-response counts by service and borough for cells meeting the minimum response threshold; this is a survey-count heatmap, not a count of integrated cells.", 5.9)

    add_heading(doc, "3.3 Text preprocessing and NLP feature extraction", 2)
    add_text(doc, f"Missing resolution descriptions were normalised before applying the common text-processing steps. VADER produced compound scores and positive, neutral, and negative rates for each record. We then aggregated the scores to the cell level using means, standard deviations, and polarity proportions. VADER was compared with RSAT satisfaction polarity on {vader['number_of_matched_cells']:,} matched cells, but it was used only as a baseline and not as a source of training labels.")
    add_text(doc, f"For topic discovery, Gensim LDA was fitted with {topics['lda']['num_topics']} topics and evaluated with C_v coherence. BERTopic used all-MiniLM-L6-v2 embeddings, density-based clustering, and class-based TF-IDF, producing {topics['bertopic']['num_topics_discovered']} non-outlier clusters. Both models were fitted only on {topics['lda']['fit_period']}; later texts were transformed without refitting. LDA and BERTopic assignments, topic entropy, and outlier rates were aggregated to analysis cells.")
    add_text(doc, f"Each supervised ABSA example begins as one RSAT row: the agency-authored resolution_description and standardised dissatisfaction_reason are fields in that same survey record. The eight raw reasons are mapped to six classes: Information Intake, Issue Correction, Other, Response Time, Status Updates, and Work Quality. This pairing does not use or claim a direct join to the separate 311 request dataset.")
    add_text(doc, f"The source has {absa['duplicate_control']['raw_labelled_rows']:,} labelled rows but only {absa['duplicate_control']['unique_normalized_descriptions']:,} normalised descriptions. Each text group is assigned to its first observed year, only labels observed in that first year are retained, and one example per text-label pair remains. This yields {absa['duplicate_control']['unique_text_label_pairs']:,} examples with zero text overlap across the 2023 train, 2024 validation, and 2025 test splits. The trained TF-IDF model is then applied to 311 resolution descriptions to create cell-level aspect rates.")
    add_text(doc, f"DistilBERT (distilbert-base-uncased) was fine-tuned locally with AdamW, learning rate {transformer['hyperparameters']['learning_rate']:.1e}, batch size {transformer['hyperparameters']['batch_size']}, maximum length {transformer['hyperparameters']['max_seq_length']}, and {transformer['hyperparameters']['epochs']} epochs. Rule, TF-IDF, and DistilBERT are evaluated on the same {absa['test_sample_count']:,}-example duplicate-controlled test split. Because citizen comments are privacy-suppressed, this remains a domain-transfer experiment rather than a human-annotated evaluation of citizen prose.")
    add_figure(doc, "absa_per_aspect_f1.png", "Figure 2. Per-aspect F1 comparison for rule, TF-IDF, and DistilBERT grievance classifiers on the same duplicate-controlled 2025 test split.", 5.85)
    add_text(doc, "For operational feature generation, the TF-IDF classifier is fitted on the duplicate-controlled 2023 RSAT training portion before application to 311 narratives. VADER is a fixed lexicon method. LDA and BERTopic are fitted only on training-period 311 text and then frozen for later-month transformation.")

    add_heading(doc, "3.4 Operational outcomes", 2)
    add_text(doc, f"""Resolution delay was calculated from valid created and closed timestamps. The raw values have a long right tail, so the primary modelling outcome was winsorised at the 99th percentile, or {outcomes['resolution_delay']['p99_delay_hours_winsorization_threshold']:.2f} hours. We report the raw median together with the winsorised mean so that the typical case and the overall operational scale are both visible.

    Repeat requests were identified from consecutive records matching borough, complaint type, and cleaned incident address. Including borough prevents identical street strings in different boroughs from being linked. Blank or UNKNOWN addresses cannot create a repeat, but they remain in the denominator. The preceding request had to occur more than 0 and no more than the selected 7-, 14-, or 30-day window. These are operational recurrence indicators, not proof that the same resident or underlying incident returned. Sensitivity checks report Heat/Hot Water, a broader housing-service proxy, and high-volume borough-address groups; the public extract has no authoritative building-type field.""")
    add_figure(doc, "nyc311_delay_hist.png", "Figure 3. Resolution-delay distribution for the selected municipal services; the long right tail motivates winsorisation before prediction.", 5.85)

    add_heading(doc, "3.5 Experimental design and statistical analysis", 2)
    add_text(doc, f"""After feature integration and one-month alignment, the primary modelling file contained {predictive['lagged_cells']:,} cells. The split used {split_counts.get('train', 0):,} training cells predicting February-August 2023, {split_counts.get('val', 0):,} validation cells predicting September-December 2023, and {split_counts.get('test', 0):,} untouched cells predicting January-December 2024. The 2025 split used for ABSA is a separate text-classification experiment.

    Ridge regression, Random Forest, and LightGBM were compared. For a single coherent primary analysis, LightGBM is used for both targets in the headline comparison, the robustness runs, the SHAP analysis, and the dashboard evidence; Ridge and Random Forest are comparison models. We also report last-value and 12-month seasonal-naive baselines. The reported p-value is from a two-sided paired t-test on per-cell absolute errors for baseline and augmented predictions. It is not a direct significance test of the R-squared difference. A negative Delta R-squared or a higher augmented MAE means that the language/satisfaction model performed worse. Cells share service and borough structure, so this test is supporting evidence rather than request-level inference.

    The same LightGBM recipe is used in the primary and robustness analyses: 100 trees, maximum depth six, learning rate 0.05, row subsampling 0.85, feature subsampling 0.90, and matched random seeds. Five seeds are evaluated after fitting on train plus validation cells. Two thousand bootstrap replicates resample the held-out cells and evaluate the mean prediction across seeds. SHAP TreeExplainer is used for global model interpretation. The dashboard ranking is evaluated separately with Precision@k, lift over random, and NDCG@k.""")
    add_table(doc, ["Partition", "Period", "Cells", "Purpose"], [
        ["Train", "Targets Feb-Aug 2023", f"{split_counts.get('train', 0):,}", "Fit models"],
        ["Validation", "Targets Sep-Dec 2023", f"{split_counts.get('val', 0):,}", "Select algorithm/features"],
        ["Out-of-time test", "Targets Jan-Dec 2024", f"{split_counts.get('test', 0):,}", "Final held-out evaluation"],
    ], [1.35, 1.55, 0.85, 2.8], "Table 4. Chronological partitions used for the integrated operational modelling experiment.")

    add_heading(doc, "3.6 Reproducibility and dashboard implementation", 2)
    add_text(doc, "The project is implemented in Python with PyTorch, Hugging Face Transformers, LightGBM, scikit-learn, Gensim, BERTopic, NLTK VADER, Parquet, and Streamlit. The accompanying project archive contains configuration files, processed feature tables, metric JSON files, figures, model artifacts, and a 20-test pytest suite. The dashboard has two views: municipal staff can inspect priority cells, trends, borough comparisons, and model evidence; residents can see aggregate service indicators in plain language. Names, addresses, and raw personal ticket text are not shown. Raw data access is documented through the two NYC Open Data identifiers in the Data availability statement.")

    add_heading(doc, "4. Results", 1)
    add_heading(doc, "4.1 Descriptive and NLP results", 2)
    add_text(doc, f"In the validated RSAT sample, 62.14% of responses are classified as dissatisfied. Issue Correction is the largest standardised grievance category. On {vader['number_of_matched_cells']:,} robust matched cells, VADER reached {vader['overall_accuracy']:.4f} accuracy and {vader['per_class']['Negative']['f1_score']:.4f} negative-class F1. Its macro-F1 was {vader['macro_f1']:.4f}, showing that performance was not balanced across classes.")
    add_table(doc, ["Component", "Evaluation", "Metric", "Result"], [
        ["VADER", f"{vader['number_of_matched_cells']:,} matched cells", "Accuracy", f"{vader['overall_accuracy']:.4f}"],
        ["VADER", f"{vader['number_of_matched_cells']:,} matched cells", "Negative F1", f"{vader['per_class']['Negative']['f1_score']:.4f}"],
        ["LDA", topics['lda']['fit_period'], "C_v coherence", f"{topics['lda']['coherence_c_v']:.4f}"],
        ["BERTopic", topics['bertopic']['fit_period'], "Clusters", str(topics['bertopic']['num_topics_discovered'])],
        ["Rule ABSA", "Common deduplicated test", "Macro-F1", f"{absa_rule['macro_f1']:.4f}"],
        ["TF-IDF ABSA", "Common deduplicated test", "Macro-F1", f"{absa_tfidf['macro_f1']:.4f}"],
        ["DistilBERT ABSA", "Common deduplicated test", "Macro-F1", f"{transformer_test['test_macro_f1']:.4f}"],
    ], [1.35, 2.25, 1.4, 1.55], "Table 5. Summary of sentiment, topic, and grievance-classification results.")
    add_text(doc, f"On the strict common test, the rule baseline reached macro-F1 {absa_rule['macro_f1']:.4f}, TF-IDF reached {absa_tfidf['macro_f1']:.4f}, and DistilBERT reached {transformer_test['test_macro_f1']:.4f}. With six classes, uniform random macro-F1 is approximately 0.167, so these results are at or below chance level. The aspect-rate features are therefore retained as a documented failure of agency boilerplate to provide a reliable proxy for citizen voice, not as evidence of successful ABSA. Duplicate removal substantially lowers the apparent sample size and may reverse conclusions drawn from the earlier duplicate-heavy evaluation. Per-class F1 is reported because the aspect distribution is imbalanced.")

    add_heading(doc, "4.2 Operational outcome distributions", 2)
    add_text(doc, f"For {outcomes['resolution_delay']['total_records']:,} service requests, the median raw delay was {outcomes['resolution_delay']['median_raw_delay_hours']:.2f} hours. The 95th percentile was {outcomes['resolution_delay']['p95_delay_hours']:.2f} hours, and the 99th-percentile winsorisation cutoff was {outcomes['resolution_delay']['p99_delay_hours_winsorization_threshold']:.2f} hours. Repeat rates were {outcomes['repeat_request_rates']['repeat_rate_7d_pct']:.2f}% at 7 days, {outcomes['repeat_request_rates']['repeat_rate_14d_pct']:.2f}% at 14 days, and {outcomes['repeat_request_rates']['repeat_rate_30d_pct']:.2f}% at 30 days.")
    add_text(doc, f"Heat/Hot Water contributes {repeat_sensitivity['heat_hot_water']['share_of_all_repeat_flags']:.2%} of 14-day repeat flags; excluding it changes the rate to {repeat_sensitivity['excluding_heat_hot_water']['repeat_rate_14d']:.2%}. A broader housing-service proxy contributes {repeat_sensitivity['housing_service_proxy']['share_of_all_repeat_flags']:.2%}; excluding those services gives {repeat_sensitivity['excluding_housing_service_proxy']['repeat_rate_14d']:.2%}. High-volume borough-address groups account for {repeat_sensitivity['high_volume_address_proxy']['share_of_all_repeat_flags']:.2%} of flags. These proxies explain concentration but do not identify building type.")
    add_figure(doc, "nyc311_monthly_volume.png", "Figure 4. Monthly NYC 311 request volume by borough. All 24 operational months from January 2023 through December 2024 are present.", 5.85)

    naive_rows = []
    for target_label, target_key in [("Mean delay (hours)", "mean_resolution_delay_hours"), ("Repeat rate (14d)", "repeat_request_rate_14d")]:
        for baseline_name, values in review["naive_baselines"][target_key].items():
            label = "Last-value (previous month)" if baseline_name == "last_value" else "Seasonal-naive (same month, previous year)"
            naive_rows.append([target_label, label, f"{values['r2']:.4f}", f"{values['mae']:.4f}", f"{values['rmse']:.4f}"])
    add_table(doc, ["Target", "Baseline", "R2", "MAE", "RMSE"], naive_rows, [1.35, 2.55, 0.85, 0.85, 0.85], "Table 6. Naive forecasting baselines on the untouched 2024 cells. The last-value baseline uses the previous month's outcome for the same service-borough cell; the seasonal-naive baseline uses the same calendar month one year earlier, with documented aggregate fallback when a cell is absent.")

    ablation_rows = []
    for target_label, target_key in [("Mean delay (hours)", "mean_resolution_delay_hours"), ("Repeat rate (14d)", "repeat_request_rate_14d")]:
        family_results = review["feature_family_ablations"][target_key]
        for family in ["VADER", "topics", "ABSA", "RSAT satisfaction"]:
            result = family_results["families"][family]
            ablation_rows.append([target_label, family, f"{result['metrics']['r2']:.4f}", f"{result['delta_r2_vs_structured']:+.4f}", f"{result['metrics']['mae']:.4f}"])
    add_table(doc, ["Target", "Added family", "R2", "Delta R2 vs structured", "MAE"], ablation_rows, [1.35, 1.45, 0.8, 1.35, 0.8], "Table 7. LightGBM feature-family ablations on the untouched 2024 cells. Each row adds one family to the same structured features; the all-family result is reported in Table 8.")

    add_heading(doc, "4.3 Out-of-time predictive comparison", 2)
    add_text(doc, f"The primary LightGBM delay model changed held-out R-squared from {delay_result['baseline']['test_metrics']['r2']:.4f} to {delay_result['augmented']['test_metrics']['r2']:.4f} (Delta {delay_result['delta_r2']:+.4f}); the augmented model was worse and its paired absolute-error p-value was {delay_result['paired_ttest_p_value']:.4g}. For repeat rate, the primary LightGBM model changed from {repeat_result['baseline']['test_metrics']['r2']:.4f} to {repeat_result['augmented']['test_metrics']['r2']:.4f} (Delta {repeat_result['delta_r2']:+.4f}); the augmented model was slightly better, with paired absolute-error p-value {repeat_result['paired_ttest_p_value']:.4g}. These p-values test error direction, not the Delta R-squared itself. The strongest structured benchmark is the last-value baseline for both outcomes, so the NLP comparison does not establish improvement over persistence. Across learned model families, the best augmented delay result was {delay_best_aug_name} at {delay_best_aug['augmented']['test_metrics']['r2']:.4f}, compared with the best structured learned result {delay_best_base_name} at {delay_best_base['baseline']['test_metrics']['r2']:.4f}; for repeat rate the corresponding values were {repeat_best_aug_name} ({repeat_best_aug['augmented']['test_metrics']['r2']:.4f}) and {repeat_best_base_name} ({repeat_best_base['baseline']['test_metrics']['r2']:.4f}).")
    add_table(doc, ["Target", "Algorithm", "Baseline R2", "Augmented R2", "Delta R2", "paired-error p"], predictive_rows, [1.5, 1.35, 1.0, 1.0, 0.9, 0.75], "Table 8. One-month-ahead 2024 R-squared comparison across learned models. The p-value tests paired absolute cell errors; it is not a direct significance test of the R-squared difference. The sign of Delta R-squared indicates whether the augmented model improved or worsened performance.")
    add_table(doc, ["Target / model", "MAE", "RMSE"], [
        [f"Delay / structured {delay_selected}", f"{delay_result['baseline']['test_metrics']['mae']:.4f} h", f"{delay_result['baseline']['test_metrics']['rmse']:.4f} h"],
        [f"Delay / augmented {delay_selected}", f"{delay_result['augmented']['test_metrics']['mae']:.4f} h", f"{delay_result['augmented']['test_metrics']['rmse']:.4f} h"],
        [f"Repeat / structured {repeat_selected}", f"{repeat_result['baseline']['test_metrics']['mae']:.4f}", f"{repeat_result['baseline']['test_metrics']['rmse']:.4f}"],
        [f"Repeat / augmented {repeat_selected}", f"{repeat_result['augmented']['test_metrics']['mae']:.4f}", f"{repeat_result['augmented']['test_metrics']['rmse']:.4f}"],
    ], [3.4, 1.2, 1.2], "Table 9. Mean absolute error and root mean squared error for the primary LightGBM comparisons on the 2024 out-of-time cells.")
    add_figure(doc, "lagged_model_r2_comparison.png", "Figure 5. One-month-ahead out-of-time R-squared comparison for structured and NLP-augmented models across the three algorithms.", 5.85)

    add_heading(doc, "4.4 Robustness and uncertainty", 2)
    add_text(doc, f"Using the exact primary LightGBM recipe across five seeds, the mean delay Delta R-squared was {delay_robust['aggregate']['delta_r2']['mean']:+.4f} with standard deviation {delay_robust['aggregate']['delta_r2']['std']:.4f}. Its bootstrap 95% interval was [{delay_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {delay_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}]. The mean repeat-rate Delta R-squared was {repeat_robust['aggregate']['delta_r2']['mean']:+.4f} with standard deviation {repeat_robust['aggregate']['delta_r2']['std']:.4f}; its interval was [{repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['lower_95']:+.4f}, {repeat_robust['bootstrap_95_percent_intervals']['delta_r2']['upper_95']:+.4f}].")
    add_figure(doc, "robustness_delta_r2.png", "Figure 6. Multi-seed incremental R-squared with error bars. Separate outcome-specific scales keep the near-zero repeat-rate change visible.", 5.85)

    add_heading(doc, "4.5 Model interpretation", 2)
    add_text(doc, "SHAP values are computed for the one-month-ahead augmented LightGBM delay model. They describe how month-t variables contribute to month-(t+1) predictions. A high SHAP importance is associative and does not mean that intervening on that variable would necessarily change delay.")
    add_figure(doc, "lagged_shap_feature_importance.png", "Figure 7. Global SHAP feature importance for the one-month-ahead augmented LightGBM delay model.", 5.85)

    add_heading(doc, "4.6 Implementation verification", 2)
    add_text(doc, "The project includes complete ingestion, preprocessing, feature aggregation, modelling, dashboard, and reporting code. Automated tests cover data contracts, sentiment thresholds, outcome logic, lag alignment, borough-aware repeat detection, duplicate-text leakage, ranking precision, and dashboard requirements. The municipal dashboard exposes the held-out one-month-ahead queue and its Precision@k evidence; the resident view presents privacy-safe historical summaries.")
    ranking_rows = []
    for k, values in ranking["metrics_by_k"].items():
        ranking_rows.append([str(k), f"{values['precision_at_k']:.3f}", f"{values['lift_over_random']:.2f}", f"{values['ndcg_at_k']:.3f}"])
    add_table(doc, ["k", "Precision@k", "Lift over random", "NDCG@k"], ranking_rows, [0.65, 1.25, 1.45, 1.05], "Table 10. Held-out 2024 dashboard priority-ranking performance. Relevance is defined from the observed composite operational burden, not from individual resident outcomes.")

    add_heading(doc, "5. Discussion", 1)
    add_text(doc, f"For delay, the primary LightGBM model produced a within-algorithm Delta R-squared of {delay_result['delta_r2']:+.4f}; the augmented model was worse and the paired absolute-error p-value was {delay_result['paired_ttest_p_value']:.4g}. For repeat rate, the primary LightGBM difference was {repeat_result['delta_r2']:+.4f}; the augmented model was slightly better but its paired absolute-error p-value was {repeat_result['paired_ttest_p_value']:.4g}. The last-value baseline was stronger than both learned model families for both targets. These comparisons therefore frame the study as a negative or near-null test of incremental language value, rather than evidence that NLP beats operational persistence.")
    add_text(doc, f"Repeat behaviour requires particular care. It depends on reporting habits, unresolved conditions, address-level recurrence, seasonal events, and the chosen repeat definition. The concentration analysis shows that high-volume addresses account for {repeat_sensitivity['high_volume_address_proxy']['share_of_all_repeat_flags']:.2%} of repeat flags. The signal can therefore be operationally useful without proving resident-level dissatisfaction or failure.")
    add_text(doc, "This work adds an outcome-prediction test to earlier 311 studies rather than treating sentiment as the final result. It also connects topic and grievance features to delay and recurrence, which are often left separate in civic NLP work. The findings remain consistent with warnings about domain shift, reporting bias, and public-sector data quality [3, 9, 10].")
    add_text(doc, "The ABSA scores should not be compared directly with product-review scores because these municipal descriptions are agency-authored, often formulaic, and only indirectly connected to citizen voice.")
    add_text(doc, "The practical use is a prioritisation workflow, not an automatic decision system. Staff can use the dashboard to find service-borough-month cells with high delay risk, repeat activity, dissatisfaction, or negative language signals. The model and SHAP results can support review and resource allocation, but they should not be used to deny service, rank individual residents, or replace staff judgement. The resident view can show aggregate performance without crossing the privacy boundary of the source data.")
    add_text(doc, f"There are several limitations. RSAT suppresses open-ended comments, so ABSA is a domain-transfer evaluation of agency narratives rather than a human-validated study of citizen prose. The study covers one city and one held-out year. ABSA has only {absa['duplicate_control']['unique_normalized_descriptions']:,} distinct normalised descriptions despite many survey rows, and label ambiguity remains.")
    add_text(doc, "Address recurrence is not the same as a verified repeated incident, and the selected fields do not identify multi-unit buildings. Cells sharing services and boroughs are not fully independent, so paired error tests are supporting evidence rather than definitive population inference. The reproducibility archive is prepared, but a DOI requires upload through an author-owned repository account.")

    add_heading(doc, "6. Conclusion", 1)
    add_text(doc, f"This project tested whether language and satisfaction signals improve aggregate municipal service monitoring. A complete {nyc_count:,}-record operational extract and {rsat_count:,} survey responses were combined at privacy-safe service-borough-month grain. The primary design uses train-only topic models, duplicate-controlled ABSA, and month-t features to predict month-(t+1) outcomes on {split_counts.get('test', 0):,} held-out 2024 cells. Against the primary LightGBM structured model, the augmented delay model changed R-squared by {delay_result['delta_r2']:+.4f}, while the repeat-rate difference was {repeat_result['delta_r2']:+.4f}. Both results are weaker than the simple last-value baselines, so the evidence does not support a general claim that NLP improves one-month-ahead prediction. These are predictive, algorithm-specific results rather than causal or universal claims. The dashboard turns the model into a review queue whose held-out ranking quality is reported with Precision@k. External-city validation and human annotation of genuine citizen text remain important future work.", size=10.5)

    add_heading(doc, "Declarations", 1)
    add_text(doc, "Acknowledgements. The authors thank Dr. Kalaavathi B for academic guidance and the Vellore Institute of Technology School of Computer Science and Engineering for the project setting.")
    add_text(doc, "Funding. This research received no specific grant from any funding agency.")
    add_text(doc, "Conflict of interest. The authors declare no conflict of interest.")
    add_text(doc, "Data availability. The study uses public NYC Open Data Socrata datasets erm2-nwe9 and 5ijn-vbdv. Raw records can be reconstructed with the documented paged queries. Code, configuration, processed cell tables, metric JSON files, figures, citation metadata, and reproducibility instructions are included in the Team 16 archive. A permanent DOI will be added after an author uploads the prepared archive to Zenodo.")
    add_text(doc, "Author contributions. Taher Panbiharwala: conceptualisation, methodology, software, formal analysis, and writing - original draft. Sanidhya Bhandari: methodology, data curation, validation, software, and writing - review and editing. Chinmoy Deb: investigation, visualisation, dashboard implementation, validation, and writing - review and editing. All authors approved the manuscript and accept responsibility for the work.")
    add_text(doc, "Ethics and privacy. The study uses public, aggregate, and privacy-constrained data. RSAT open-text comments are not used because the public records suppress them. No individual-level prediction or disclosure is performed.")
    add_text(doc, "Declaration of generative AI assistance. Generative AI tools were used to support code review, language editing, and document formatting. The authors inspected the source data, executed the analyses, verified every reported metric against saved artifacts, and accept full responsibility for the manuscript.")

    add_heading(doc, "References", 1)
    refs = [
        "[1] Wang, L., Qian, C., Kats, P., Kontokosta, C., and Sobolevsky, S. (2017). Structure of 311 service requests as a signature of urban location. PLOS ONE, 12(10), e0186314.",
        "[2] Li, Y., Hyder, A., Southerland, L.T., Hammond, G., Miller, H.J., and Porr, A. (2020). 311 service requests as indicators of neighbourhood distress and opioid use disorder. Scientific Reports, 10, 19579.",
        "[3] Kontokosta, C.E., and Hong, B. (2021). Bias in smart city governance: How socio-spatial disparities in 311 complaint behavior impact the fairness of data-driven decisions. Sustainable Cities and Society, 64, 102503.",
        "[4] Boxer, K.S., Hong, B., Kontokosta, C.E., and Neill, D.B. (2025). Estimating reporting bias in 311 complaint data. The Annals of Applied Statistics, 19(2).",
        "[5] Hutto, C.J., and Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. Proceedings of ICWSM.",
        "[6] Devlin, J., Chang, M.W., Lee, K., and Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. Proceedings of NAACL-HLT, 4171-4186.",
        "[7] Blei, D.M., Ng, A.Y., and Jordan, M.I. (2003). Latent Dirichlet allocation. Journal of Machine Learning Research, 3, 993-1022.",
        "[8] Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv preprint arXiv:2203.05794.",
        "[9] Zhang, W., Li, X., Deng, Y., Bing, L., and Lam, W. (2022). A survey on aspect-based sentiment analysis: Tasks, methods, and challenges. IEEE Transactions on Knowledge and Data Engineering, 35(11), 11019-11038.",
        "[10] Chauhan, G.S., Nahta, R., Meena, Y.K., and Gopalani, D. (2023). Aspect based sentiment analysis using deep learning approaches: A survey. Computer Science Review, 49, 100576.",
        "[11] Nazir, A., Rao, Y., Wu, L., and Sun, L. (2022). Issues and challenges of aspect-based sentiment analysis: A comprehensive survey. IEEE Transactions on Affective Computing, 13(2), 845-863.",
        "[12] Hua, Y.C., Denny, P., Wicker, J., and Taskova, K. (2024). A systematic review of aspect-based sentiment analysis: Domains, methods, and trends. Artificial Intelligence Review, 57(11), 296.",
        "[13] Wankhade, M., Rao, A.C.S., and Kulkarni, C. (2022). A survey on sentiment analysis methods, applications, and challenges. Artificial Intelligence Review, 55(7), 5731-5780.",
        "[14] Barik, K., and Misra, S. (2024). Analysis of customer reviews with an improved VADER lexicon classifier. Journal of Big Data, 11(1), 10.",
        "[15] Tang, Z., Pan, X., and Gu, Z. (2024). Analyzing public demands on China's online government inquiry platform: A BERTopic-based topic modeling study. PLOS ONE, 19(2), e0296855.",
        "[16] Liu, J., Long, R., Chen, H., Wu, M., Ma, W., and Li, Q. (2024). Topic-sentiment analysis of citizen environmental complaints in China using a Stacking-BERT model. Journal of Environmental Management, 371, 123112.",
        "[17] Li, C., Tian, Q., Gao, L., and Liu, H. (2026). Public feedback analysis on multi-stage emergency management policies using a BERTopic-SKEP integrated model. Scientific Reports, 16, 684.",
        "[18] Malik, T., Tahir, A., Bilal, A., Dashtipour, K., Imran, M.A., and Abbasi, Q.H. (2022). Social sensing for sentiment analysis of policing authority performance in smart cities. Frontiers in Communications and Networks, 2, 821090.",
        "[19] Fu, X., Sanchez, T.W., Li, C., and Reu Junqueira, J. (2024). Deciphering public voices in the digital era: Benchmarking ChatGPT for analysing citizen feedback in Hamilton, New Zealand. Journal of the American Planning Association, 90(4), 728-741.",
        "[20] Tai, T.-E., Haw, S.-C., Kong, W.-E., and Ng, K.-W. (2024). Performance evaluation of machine-learning techniques on resolution-time prediction in helpdesk support systems. International Journal on Robotics, Automation and Sciences, 6(2), 59-68.",
        "[21] Zhang, H., and Shafiq, M.O. (2024). Survey of transformers and towards ensemble learning using transformers for NLP. Journal of Big Data, 11(1), 25.",
        "[22] Perikos, I., and Diamantopoulos, A. (2024). Explainable aspect-based sentiment analysis using transformer models. Big Data and Cognitive Computing, 8(11), 141.",
        "[23] Yu, B., and Zhang, S. (2023). A novel weight-oriented graph convolutional network for aspect-based sentiment analysis. The Journal of Supercomputing, 79(1), 947-972.",
        "[24] Zhang, Y., Yang, Y., Liang, B., Chen, S., Qin, B., and Xu, R. (2023). An empirical study of sentiment-enhanced pre-training for ABSA. Findings of ACL 2023, 9633-9651.",
        "[25] Lore, M., Harten, J.G., and Boeing, G. (2024). A hybrid deep learning method for identifying topics in large-scale urban text data. Computers, Environment and Urban Systems, 111, 102131.",
        "[26] Ghahramani, M., Galle, N.J., Ratti, C., and Pilla, F. (2021). Tales of a city: Sentiment analysis of urban green space in Dublin. Cities, 119, 103395.",
        "[27] Haghighi, N.N., Liu, X.C., Wei, R., Li, W., and Shao, H. (2018). Using Twitter data for transit performance assessment. Public Transport, 10, 363-377.",
        "[28] NYC Open Data. (n.d.). 311 Service Requests from 2010 to Present. New York City Open Data, dataset erm2-nwe9.",
        "[29] NYC Office of Technology and Innovation. (2025). 311 Resolution Satisfaction Survey. New York City Open Data, dataset 5ijn-vbdv.",
        "[30] Aggarwal, I., Joseph, S., Jaganathan, N., Patel, A., Kumar, V., and Devarapalli, M. (2025). Sentiment analysis in healthcare: A comparison of VADER, BERT, and Flair NLP models. Cureus, 17(7), e88902.",
    ]
    for ref in refs:
        add_reference(doc, ref)

    # Apply true subscript/superscript formatting across body paragraphs and
    # table cells after all dynamic text has been generated.
    for paragraph in doc.paragraphs:
        format_math_notation(paragraph)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    format_math_notation(paragraph)

    # Footer with a simple field-like page number placeholder.
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.text = "Citizen Sentiment Analysis | BCSE316L | Page "
    r = fp.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r._r.addnext(fld)
    for run in fp.runs:
        set_run_font(run, 8.5, color="666666")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print(OUT)


if __name__ == "__main__":
    main()
