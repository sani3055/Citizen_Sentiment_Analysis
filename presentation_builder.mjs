import pptxgen from 'pptxgenjs';
import fs from 'node:fs';
import path from 'node:path';

const root = 'D:/CITY PRJ';
const outDir = path.join(root, 'outputs');
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, 'Citizen_Sentiment_Analysis_Review2_Final_Review.pptx');
const figDir = path.join(root, 'reports', 'figures');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'BCSE316L Project Team 16';
pptx.subject = 'Citizen Sentiment Analysis of Municipal Services Using Transformer-Based NLP';
pptx.title = 'Review-2 / Final Review Presentation';
pptx.company = 'Vellore Institute of Technology';
pptx.lang = 'en-US';
pptx.theme = { headFontFace: 'Aptos Display', bodyFontFace: 'Aptos', lang: 'en-US' };
pptx.defineSlideMaster({
  title: 'DARK',
  background: { color: '0B1220' },
  objects: [],
  slideNumber: { x: 12.15, y: 7.12, color: '9FB2C3', fontFace: 'Aptos', fontSize: 9 },
});

const C = {
  bg: '0B1220', panel: '111C2C', panel2: '18263A', text: 'F0F6FC', muted: 'B8C7D6',
  cyan: '4CC9F0', teal: '1F6F8B', green: '52B788', amber: 'F6BD60', red: 'FF6B6B', line: '294158',
};

const presenterNotes = {
  2: '1. Traditional KPIs measure ticket volume and closure time, but not citizen experience.\n2. Our study tests whether NLP adds useful evidence for municipal service prediction.',
  3: '1. A ticket marked closed does not always mean that the citizen feels the issue was solved.\n2. We connect operational complaints with citizen dissatisfaction signals.',
  4: '1. We compare a structured-data model with a model that also uses NLP features.\n2. The results show predictive association and do not claim cause and effect.',
  5: '1. The NYC 311 dataset contains 1,199,279 service-request records.\n2. The RSAT dataset contains 406,581 satisfaction survey responses.',
  6: '1. We aggregate both sources by service, borough, year, and month for privacy-safe integration.\n2. Chronological splits prevent future information from entering earlier predictions.',
  7: '1. Approximately 62.14% of validated survey responses were dissatisfied.\n2. This confirms that citizen dissatisfaction is a meaningful research signal.',
  8: '1. VADER provides a simple sentiment baseline for comparison.\n2. Topic models, ABSA, and DistilBERT provide deeper language analysis.',
  9: '1. DistilBERT achieved a test macro-F1 score of 0.3491.\n2. It performed better than both TF-IDF and the rule-based classification approach.',
  10: '1. The median resolution delay was 2.90 hours across the service records.\n2. The 14-day repeat-request rate was 44.88%, showing recurring demand.',
  11: '1. The baseline model uses service, borough, month, seasonality, and request volume.\n2. The augmented model adds sentiment, topic, grievance, and satisfaction features.',
  12: '1. Delay prediction improved from R² 0.5149 to 0.5438 with NLP features.\n2. Repeat-rate performance improved slightly, but the result was not statistically significant.',
  13: '1. We used five random seeds and 2,000 bootstrap samples to test stability.\n2. Delay gains were reliable, while repeat-rate gains remained uncertain.',
  14: '1. SHAP explains which features contribute most to each model prediction.\n2. Request volume, topics, response time, seasonality, and negative sentiment were important.',
  15: '1. Municipal officials can view priorities, trends, comparisons, and model evidence.\n2. Residents can view simple aggregate service information without personal data.',
  16: '1. The complete data, NLP, modeling, dashboard, and reporting pipeline is implemented.\n2. All 16 automated tests are passing successfully.',
  17: '1. The project reports predictive relationships and does not claim causation.\n2. Future work includes manual annotation, longer testing, and external validation.',
};

const fig = (name) => path.join(figDir, name);
const exists = (p) => fs.existsSync(p);

function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h, fontFace: opts.fontFace || 'Aptos', fontSize: opts.fontSize || 16,
    color: opts.color || C.text, bold: opts.bold || false, align: opts.align || 'left',
    valign: opts.valign || 'mid', margin: opts.margin ?? 0, breakLine: false,
    fit: 'shrink', paraSpaceAfterPt: 0, bullet: opts.bullet,
    italic: opts.italic || false, charSpacing: opts.charSpacing || 0,
  });
}

// 15. Dashboard
{
  const s = baseSlide('The final system turns the analysis into two decision-support views', 'Interactive dashboard', 15);
  rect(s, 0.75, 1.62, 5.45, 3.7, C.panel, 0.12, C.line);
  addText(s, 'Municipal Operations', 1.05, 1.96, 4.1, 0.3, { fontSize: 19, color: C.cyan, bold: true });
  bullets(s, ['Filter by borough, service, and period', 'Priority queue with risk score', 'Trend and borough comparison charts', 'Model evidence and SHAP view', 'Downloadable priority queue'], 1.05, 2.5, 4.65, 14.5, 0.43);
  rect(s, 6.72, 1.62, 5.45, 3.7, C.panel, 0.12, C.line);
  addText(s, 'Resident View', 7.02, 1.96, 4.1, 0.3, { fontSize: 19, color: C.amber, bold: true });
  bullets(s, ['Plain-language KPI summary', 'Historical delay and repeat trends', 'Citywide service comparison', 'Privacy-safe aggregate values', 'No names, addresses, or ticket text'], 7.02, 2.5, 4.65, 14.5, 0.43);
  addText(s, 'Live local link', 0.75, 5.75, 1.45, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'http://localhost:8501', 2.35, 5.72, 3.6, 0.28, { fontSize: 18, bold: true, fontFace: 'Aptos Display' });
  addText(s, 'Data grain: service × borough × month', 7.8, 5.75, 4.35, 0.22, { fontSize: 14, color: C.muted, align: 'right' });
}

// 16. Implementation status
{
  const s = baseSlide('All major pipeline phases are implemented with inspectable artifacts', 'Implementation status', 16);
  addText(s, 'Completed pipeline', 0.75, 1.65, 2.6, 0.28, { fontSize: 19, color: C.cyan, bold: true });
  const labels = ['Audit', 'Environment', 'Ingestion', 'EDA', 'NLP', 'Outcomes', 'Integration', 'Modeling', 'Transformer', 'Dashboard', 'Tests', 'Report'];
  const colors = [C.green, C.green, C.green, C.green, C.cyan, C.cyan, C.cyan, C.amber, C.amber, C.red, C.green, C.green];
  labels.forEach((label, i) => {
    const col = i % 6; const row = Math.floor(i / 6); const x = 0.75 + col * 1.95; const y = 2.2 + row * 0.88;
    rect(s, x, y, 1.68, 0.58, C.panel, 0.1, C.line);
    rect(s, x, y, 0.08, 0.58, colors[i], 0.03, colors[i]);
    addText(s, String(i + 1).padStart(2, '0'), x + 0.2, y + 0.11, 0.3, 0.16, { fontSize: 9.5, color: C.muted, bold: true });
    addText(s, label, x + 0.2, y + 0.3, 1.25, 0.18, { fontSize: 12.5, bold: true });
  });
  panelTitle(s, 'Current verification', 0.75, 4.55, 2.9);
  kpi(s, '16 / 16', 'pytest checks passing', 0.75, 5.0, 2.65, C.green);
  kpi(s, '108', 'environment dependencies verified', 3.7, 5.0, 3.2, C.cyan);
  kpi(s, '2024', 'operational out-of-time horizon', 7.2, 5.0, 3.0, C.amber);
}

// 17. Limitations and next steps
{
  const s = baseSlide('The project is submission-ready when its boundaries are stated clearly', 'Limitations and next steps', 17);
  rect(s, 0.75, 1.62, 5.45, 3.72, C.panel, 0.12, C.line);
  addText(s, 'What the evidence does not claim', 1.05, 1.96, 4.6, 0.3, { fontSize: 18, color: C.red, bold: true });
  bullets(s, ['No causal effect is established.', 'RSAT free-text comments are PII-suppressed.', 'ABSA is a domain-transfer evaluation.', 'Repeat-rate gain is not significant.', '2024 is the local operational test horizon.'], 1.05, 2.52, 4.65, 14.5, 0.43);
  rect(s, 6.72, 1.62, 5.45, 3.72, C.panel, 0.12, C.line);
  addText(s, 'Highest-value next steps', 7.02, 1.96, 4.2, 0.3, { fontSize: 18, color: C.green, bold: true });
  bullets(s, ['Complete two-annotator 311 ABSA sample.', 'Report Cohen’s kappa and human macro-F1.', 'Collect a longer out-of-time horizon.', 'Validate transfer on another 311 city.', 'Monitor drift before deployment.'], 7.02, 2.52, 4.65, 14.5, 0.43);
  addText(s, 'Academic position', 0.75, 5.78, 1.55, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'Strong end-to-end engineering and reproducibility; conclusions are calibrated to the available evidence.', 2.55, 5.75, 9.55, 0.28, { fontSize: 14, color: C.muted });
}

// 18. Close
{
  const s = pptx.addSlide('DARK');
  rect(s, 0.82, 1.05, 0.1, 5.1, C.cyan, 0, C.cyan);
  addText(s, 'FINAL TAKEAWAY', 1.35, 1.14, 3.2, 0.22, { fontSize: 10, color: C.cyan, bold: true, charSpacing: 1.2 });
  addText(s, 'Municipal service quality is more than closure speed.', 1.35, 1.65, 10.3, 0.72, { fontSize: 34, bold: true, fontFace: 'Aptos Display' });
  addText(s, 'This project demonstrates a reproducible way to connect citizen dissatisfaction, civic text signals, and operational outcomes — with transparent limits and an actionable dashboard.', 1.35, 2.75, 9.9, 0.85, { fontSize: 19, color: C.muted, valign: 'top' });
  rect(s, 1.35, 4.22, 10.2, 0.95, C.panel, 0.12, C.line);
  addText(s, 'Key result', 1.7, 4.53, 1.2, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'Significant incremental evidence for resolution-delay prediction; repeat-rate evidence remains a research opportunity.', 3.05, 4.43, 8.05, 0.45, { fontSize: 16, bold: true });
  addText(s, 'Thank you  •  Questions and discussion', 1.35, 6.82, 5.5, 0.2, { fontSize: 13, color: C.muted });
  presenterLine(s, '1. Service quality is more than closing tickets.\n2. NLP is especially useful for predicting delay.', 6.22);
  addText(s, '18', 12.08, 6.82, 0.55, 0.2, { fontSize: 9, color: '9FB2C3', align: 'right' });
}

// 7. EDA
{
  const s = baseSlide('The survey reveals a strongly negative satisfaction distribution', 'Exploratory findings', 7);
  addText(s, '62.14%', 0.75, 1.72, 2.5, 0.5, { fontSize: 38, color: C.red, bold: true, fontFace: 'Aptos Display' });
  addText(s, 'of validated RSAT responses are dissatisfied', 0.75, 2.32, 3.4, 0.5, { fontSize: 18, bold: true });
  addText(s, 'Issue correction is the largest standardized grievance aspect (42.7% of dissatisfied responses).', 0.75, 3.15, 3.6, 0.78, { fontSize: 15, color: C.muted, valign: 'top' });
  rect(s, 5.25, 1.62, 6.9, 3.45, C.panel, 0.12, C.line);
  image(s, fig('rsat_satisfaction_dist.png'), 5.5, 1.87, 6.4, 2.85);
  addText(s, 'RSAT satisfaction distribution', 0.75, 5.3, 3.5, 0.25, { fontSize: 17, color: C.cyan, bold: true });
  addText(s, 'This skew establishes a meaningful citizen-distress signal for later aggregation and modeling.', 3.25, 5.29, 8.9, 0.25, { fontSize: 14, color: C.muted });
}

// 8. NLP pipeline
{
  const s = baseSlide('The NLP stack moves from baselines to domain adaptation', 'NLP methodology', 8);
  const xs = [0.75, 3.55, 6.35, 9.15];
  const titles = ['VADER', 'LDA + BERTopic', 'ABSA', 'DistilBERT'];
  const subs = ['Lexicon sentiment', 'Themes and clusters', 'Six grievance aspects', 'Transformer fine-tuning'];
  const metrics = ['Accuracy 0.655\nNegative F1 0.800', 'Cᵥ 0.5100\n14 semantic clusters', 'TF-IDF macro-F1 0.1723\nRule baseline 0.1295', 'Test macro-F1 0.3491\nAccuracy 0.4148'];
  const colors = [C.cyan, C.amber, C.green, C.red];
  for (let i = 0; i < 4; i++) {
    rect(s, xs[i], 1.75, 2.35, 2.7, C.panel, 0.12, C.line);
    rect(s, xs[i], 1.75, 0.07, 2.7, colors[i], 0.03, colors[i]);
    addText(s, titles[i], xs[i] + 0.25, 2.05, 1.85, 0.28, { fontSize: 18, bold: true });
    addText(s, subs[i], xs[i] + 0.25, 2.55, 1.85, 0.35, { fontSize: 12, color: C.muted, valign: 'top' });
    addText(s, metrics[i], xs[i] + 0.25, 3.33, 1.85, 0.65, { fontSize: 14, bold: true, valign: 'top' });
  }
  line(s, 1.7, 5.05, 11.65, 5.05, C.line, 1);
  addText(s, 'Design boundary', 0.75, 5.35, 1.45, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'Resolution narratives are agency text; RSAT provides the citizen-grounded labels and satisfaction aggregates.', 2.45, 5.32, 9.6, 0.3, { fontSize: 14, color: C.muted });
}

// 9. NLP evidence
{
  const s = baseSlide('Transformer adaptation improves grievance attribution', 'NLP results', 9);
  rect(s, 0.75, 1.62, 5.3, 3.6, C.panel, 0.12, C.line);
  image(s, fig('absa_per_aspect_f1.png'), 0.98, 1.92, 4.85, 2.95);
  addText(s, 'Per-aspect F1 comparison', 0.98, 4.98, 4.3, 0.2, { fontSize: 11.5, color: C.muted });
  rect(s, 6.42, 1.62, 5.73, 3.6, C.panel, 0.12, C.line);
  addText(s, 'Transformer run', 6.8, 1.95, 3.1, 0.3, { fontSize: 19, color: C.cyan, bold: true });
  kpi(s, '0.3491', 'Out-of-time macro-F1', 6.8, 2.55, 4.95, C.green);
  kpi(s, '+0.1768', 'Macro-F1 gain vs TF-IDF', 6.8, 3.72, 4.95, C.amber);
  addText(s, 'Kaggle Tesla T4 • 3 epochs • 2e-5 learning rate\n41,746 chronological examples across train / validation / test', 6.8, 4.88, 4.95, 0.42, { fontSize: 12.5, color: C.muted, valign: 'top' });
}

// 10. Outcomes
{
  const s = baseSlide('Operational outcomes quantify both delay and recurring demand', 'Operational outcomes', 10);
  kpi(s, '2.90 h', 'Median raw resolution delay', 0.75, 1.62, 2.45, C.cyan);
  kpi(s, '91.11 h', 'Mean winsorized delay', 3.48, 1.62, 2.45, C.amber);
  kpi(s, '44.88%', '14-day repeat rate', 6.21, 1.62, 2.45, C.red);
  kpi(s, '50.52%', '30-day repeat rate', 8.94, 1.62, 2.45, C.green);
  rect(s, 0.75, 3.02, 5.3, 2.55, C.panel, 0.12, C.line);
  image(s, fig('nyc311_delay_hist.png'), 0.98, 3.25, 4.84, 1.9);
  addText(s, 'Delay is highly right-skewed; p99 winsorization cutoff = 2,454.96 hours.', 0.98, 5.27, 4.8, 0.22, { fontSize: 11.5, color: C.muted });
  rect(s, 6.42, 3.02, 5.73, 2.55, C.panel, 0.12, C.line);
  image(s, fig('nyc311_monthly_volume.png'), 6.65, 3.25, 5.26, 1.9);
  addText(s, 'Repeat rates rise with longer windows: 39.10% at 7 days → 50.52% at 30 days.', 6.65, 5.27, 5.2, 0.22, { fontSize: 11.5, color: C.muted });
}

// 11. Modeling design
{
  const s = baseSlide("The experiment isolates NLP's incremental value", 'Predictive modeling', 11);
  addText(s, 'Structured baseline', 0.75, 1.72, 3.0, 0.3, { fontSize: 19, color: C.cyan, bold: true });
  bullets(s, ['Service identity', 'Borough', 'Month seasonality', 'Request volume'], 0.75, 2.2, 3.6, 16, 0.43);
  addText(s, '→', 5.0, 2.5, 0.6, 0.45, { fontSize: 30, color: C.cyan, bold: true, align: 'center' });
  addText(s, 'NLP-augmented model', 6.2, 1.72, 3.5, 0.3, { fontSize: 19, color: C.amber, bold: true });
  bullets(s, ['All baseline features', 'VADER sentiment rates', 'LDA / BERTopic features', 'ABSA aspect proportions', 'RSAT satisfaction signals'], 6.2, 2.2, 4.4, 16, 0.39);
  panelTitle(s, 'Evaluation protocol', 0.75, 4.75, 2.9);
  rect(s, 0.75, 5.2, 11.85, 0.56, C.panel, 0.12, C.line);
  addText(s, 'Ridge  •  Random Forest  •  LightGBM   |   validation-selected algorithm   |   one untouched 2024 horizon test', 1.0, 5.36, 11.35, 0.2, { fontSize: 14, bold: true, align: 'center' });
}

// 12. Main model results
{
  const s = baseSlide('Delay gains are significant; repeat-rate gains are inconclusive', 'Main results', 12);
  rect(s, 0.75, 1.62, 5.35, 3.85, C.panel, 0.12, C.line);
  image(s, fig('model_r2_comparison.png'), 1.0, 1.9, 4.85, 3.05);
  addText(s, '2024 out-of-time R² comparison', 1.0, 5.08, 4.6, 0.2, { fontSize: 11.5, color: C.muted });
  // Use native shapes for this compact results table. This keeps contrast
  // explicit and avoids PowerPoint compatibility problems with table markup.
  const tableX = 6.42; const tableY = 1.92; const tableW = 5.73;
  const colW = [1.18, 1.26, 0.78, 0.78, 0.72, 1.01];
  const tableRows = [
    ['Target', 'Model', 'Base R²', 'Aug R²', 'ΔR²', 'p-value'],
    ['Delay (h)', 'LightGBM', '0.5149', '0.5438', '+0.0289', '0.00020'],
    ['Repeat 14d', 'LightGBM', '0.7184', '0.7441', '+0.0257', '0.733'],
  ];
  const rowH = [0.48, 0.54, 0.54];
  let rowY = tableY;
  tableRows.forEach((row, ri) => {
    rect(s, tableX, rowY, tableW, rowH[ri], ri === 0 ? C.panel2 : C.panel, 0, C.line);
    let cellX = tableX;
    row.forEach((cell, ci) => {
      addText(s, cell, cellX + 0.07, rowY + (ri === 0 ? 0.14 : 0.16), colW[ci] - 0.14, 0.2, {
        fontSize: ri === 0 ? 10 : 10.5,
        color: ri === 0 ? C.cyan : C.text,
        bold: ri === 0 || ci === 4,
        align: ci >= 2 ? 'center' : 'left',
      });
      cellX += colW[ci];
    });
    rowY += rowH[ri];
  });
  rect(s, 6.42, 3.85, 5.73, 1.15, C.panel2, 0.12, C.line);
  addText(s, 'Interpretation', 6.72, 4.08, 1.5, 0.2, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'Delay: confirmed incremental predictive association.\nRepeat: positive observed gain, but not statistically significant.', 6.72, 4.4, 4.95, 0.46, { fontSize: 14, color: C.text, valign: 'top' });
}

// 13. Robustness
{
  const s = baseSlide('Robustness confirms delay gains and qualifies repeat-rate gains', 'Uncertainty analysis', 13);
  rect(s, 0.75, 1.62, 6.05, 3.78, C.panel, 0.12, C.line);
  image(s, fig('robustness_delta_r2.png'), 0.98, 1.9, 5.6, 3.15);
  addText(s, 'Five seeds + 2,000 bootstrap resamples', 0.98, 5.12, 5.4, 0.2, { fontSize: 11.5, color: C.muted });
  rect(s, 7.12, 1.62, 5.03, 3.78, C.panel, 0.12, C.line);
  addText(s, 'Delay', 7.5, 1.95, 1.2, 0.28, { fontSize: 19, color: C.green, bold: true });
  addText(s, 'Mean ΔR²  +0.1287 ± 0.0097\n95% bootstrap CI  [+0.0499, +0.2259]', 7.5, 2.4, 4.2, 0.65, { fontSize: 16, bold: true, valign: 'top' });
  line(s, 7.5, 3.25, 11.7, 3.25, C.line, 1);
  addText(s, 'Repeat rate', 7.5, 3.55, 2.0, 0.28, { fontSize: 19, color: C.amber, bold: true });
  addText(s, 'Mean ΔR²  +0.0403 ± 0.0072\n95% bootstrap CI  [-0.0072, +0.0794]', 7.5, 4.0, 4.2, 0.65, { fontSize: 16, bold: true, valign: 'top' });
  addText(s, 'The interval crossing zero is the key qualification.', 7.5, 4.95, 4.2, 0.22, { fontSize: 12.5, color: C.muted });
}

// 14. Explainability
{
  const s = baseSlide('SHAP links predictions to operational and language signals', 'Model interpretation', 14);
  rect(s, 0.75, 1.62, 6.0, 4.05, C.panel, 0.12, C.line);
  image(s, fig('shap_feature_importance.png'), 0.98, 1.9, 5.55, 3.3);
  addText(s, 'Global SHAP feature ranking', 0.98, 5.3, 4.5, 0.2, { fontSize: 11.5, color: C.muted });
  addText(s, 'Top contributors in the augmented delay model', 7.25, 1.85, 4.4, 0.28, { fontSize: 18, color: C.cyan, bold: true });
  bullets(s, ['log_request_volume', 'topic_entropy', 'response-time aspect', 'month seasonality', 'VADER negative rate'], 7.25, 2.35, 4.0, 16, 0.43);
  addText(s, 'Meaning', 7.25, 4.75, 1.0, 0.22, { fontSize: 16, color: C.amber, bold: true });
  addText(s, 'The model uses both operational pressure and civic-language signals; the dashboard exposes these signals for review rather than hiding them behind a single score.', 7.25, 5.12, 4.7, 0.5, { fontSize: 14, color: C.muted, valign: 'top' });
}

function rect(slide, x, y, w, h, fill, radius = 0.12, line = fill) {
  slide.addShape(radius ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, {
    x, y, w, h, rectRadius: radius, fill: { color: fill }, line: { color: line, width: 0.7 },
  });
}

function line(slide, x1, y1, x2, y2, color = C.line, width = 1) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width } });
}

function image(slide, imagePath, x, y, w, h) {
  if (exists(imagePath)) slide.addImage({ path: imagePath, x, y, w, h });
  else addText(slide, `Missing figure: ${path.basename(imagePath)}`, x, y, w, h, { color: C.muted, align: 'center' });
}

function footer(slide, n) {
  line(slide, 0.67, 7.02, 12.66, 7.02, C.line, 0.7);
  addText(slide, 'BCSE316L | Design of Smart Cities', 0.67, 7.08, 4.8, 0.16, { fontSize: 8.5, color: '9FB2C3' });
  addText(slide, String(n).padStart(2, '0'), 12.08, 7.08, 0.55, 0.16, { fontSize: 8.5, color: '9FB2C3', align: 'right' });
}

function presenterLine(slide, text, y = 6.28) {
  if (!text) return;
  rect(slide, 0.67, y, 12.0, 0.56, C.panel, 0.08, C.line);
  const lines = String(text).split('\n');
  lines.slice(0, 2).forEach((lineText, i) => {
    addText(slide, lineText, 0.9, y + 0.07 + i * 0.22, 11.55, 0.16, { fontSize: 9.2, color: C.muted, italic: true });
  });
}

function baseSlide(title, eyebrow, n) {
  const slide = pptx.addSlide('DARK');
  addText(slide, eyebrow.toUpperCase(), 0.67, 0.38, 9.5, 0.18, { fontSize: 9.5, color: C.cyan, bold: true, charSpacing: 1.2 });
  addText(slide, title, 0.67, 0.7, 12.0, 0.5, { fontSize: 27, color: C.text, bold: true, fontFace: 'Aptos Display' });
  presenterLine(slide, presenterNotes[n]);
  footer(slide, n);
  return slide;
}

function panelTitle(slide, title, x, y, w) { addText(slide, title, x, y, w, 0.28, { fontSize: 17, bold: true }); }

function kpi(slide, value, label, x, y, w, accent = C.cyan) {
  rect(slide, x, y, w, 0.86, C.panel, 0.12, C.line);
  rect(slide, x, y, 0.06, 0.86, accent, 0.03, accent);
  addText(slide, value, x + 0.18, y + 0.12, w - 0.28, 0.31, { fontSize: 22, bold: true, fontFace: 'Aptos Display' });
  addText(slide, label, x + 0.18, y + 0.52, w - 0.28, 0.18, { fontSize: 10.5, color: C.muted });
}

function bullets(slide, items, x, y, w, size = 14.5, gap = 0.37) {
  items.forEach((item, i) => {
    addText(slide, '•', x, y + i * gap, 0.16, 0.2, { fontSize: size + 2, color: C.cyan, bold: true });
    addText(slide, item, x + 0.22, y + i * gap, w - 0.22, 0.3, { fontSize: size, color: C.muted });
  });
}

function addTable(slide, rows, x, y, w, h, widths, fontSize = 10.5) {
  slide.addTable(rows, {
    x, y, w, h, colW: widths, rowH: h / rows.length,
    fontFace: 'Aptos', fontSize, color: C.text, border: { type: 'solid', color: C.line, pt: 0.6 },
    fill: C.panel, margin: 0.08, valign: 'mid', breakLine: false,
    bold: false,
    autoFit: false,
    color: C.text,
  });
  const table = slide._slideObjects[slide._slideObjects.length - 1];
  return table;
}

// 1. Cover
{
  const s = pptx.addSlide('DARK');
  rect(s, 0, 0, 13.333, 0.16, C.cyan, 0, C.cyan);
  rect(s, 9.58, 0, 3.75, 7.5, C.panel, 0, C.panel);
  rect(s, 9.58, 0, 0.1, 7.5, C.cyan, 0, C.cyan);
  addText(s, 'BCSE316L  |  DESIGN OF SMART CITIES', 0.84, 0.8, 7.5, 0.24, { fontSize: 11, color: C.cyan, bold: true, charSpacing: 1.1 });
  addText(s, 'Citizen Sentiment Analysis\nof Municipal Services\nUsing Transformer-Based NLP', 0.84, 1.55, 7.7, 1.85, { fontSize: 34, bold: true, fontFace: 'Aptos Display', valign: 'top' });
  addText(s, 'Review-2 / Final Review Presentation', 0.85, 4.18, 6.8, 0.34, { fontSize: 19, color: C.muted });
  addText(s, 'Vellore Institute of Technology  •  SCOPE', 0.85, 5.02, 7.3, 0.2, { fontSize: 13.5, color: C.muted });
  addText(s, 'Guide: Dr. Kalaavathi B', 0.85, 5.34, 5.0, 0.2, { fontSize: 12.5, color: C.muted });
  addText(s, 'Taher Panbiharwala  •  Sanidhya Bhandari  •  Chinmoy Deb', 0.85, 5.68, 8.1, 0.22, { fontSize: 11.5, color: C.muted });
  addText(s, 'Project / Team 16', 0.85, 6.02, 2.8, 0.2, { fontSize: 12.5, color: C.muted });
  presenterLine(s, '1. We combine NYC 311 and satisfaction data.\n2. NLP supports municipal service prediction.', 6.28);
  addText(s, 'A reproducible civic intelligence pipeline\nfrom open data to decision support', 10.15, 2.05, 2.55, 0.82, { fontSize: 18, bold: true, fontFace: 'Aptos Display', valign: 'top' });
  line(s, 10.15, 3.12, 12.72, 3.12, C.line, 1);
  addText(s, '1.20M', 10.15, 3.45, 2.2, 0.36, { fontSize: 25, color: C.cyan, bold: true, fontFace: 'Aptos Display' });
  addText(s, '311 service requests', 10.15, 3.88, 2.3, 0.2, { fontSize: 11, color: C.muted });
  addText(s, '406.6K', 10.15, 4.42, 2.2, 0.36, { fontSize: 25, color: C.cyan, bold: true, fontFace: 'Aptos Display' });
  addText(s, 'RSAT responses', 10.15, 4.85, 2.3, 0.2, { fontSize: 11, color: C.muted });
  addText(s, 'October 2026', 0.85, 7.08, 2.0, 0.16, { fontSize: 9, color: '9FB2C3' });
}

// 2. Executive story
{
  const s = baseSlide('NLP adds evidence beyond traditional operational KPIs', 'Executive story', 2);
  addText(s, 'Core question', 0.75, 1.72, 2.4, 0.28, { fontSize: 18, color: C.cyan, bold: true });
  addText(s, 'Does adding sentiment, topic, and grievance signals improve out-of-time prediction of resolution delay and repeat complaints?', 0.75, 2.08, 4.5, 0.92, { fontSize: 19, bold: true, fontFace: 'Aptos Display', valign: 'top' });
  addText(s, 'The answer is target-specific: the corrected experiment supports a significant delay gain, while repeat-rate improvement remains an observed but uncertain signal.', 0.75, 3.25, 4.45, 0.72, { fontSize: 14.5, color: C.muted, valign: 'top' });
  kpi(s, '+0.0289', 'Delay ΔR² | p = 0.00020', 5.55, 1.74, 2.35, C.green);
  kpi(s, '+0.0257', 'Repeat ΔR² | p = 0.733', 8.12, 1.74, 2.35, C.amber);
  kpi(s, '16 / 16', 'Current automated tests passing', 5.55, 3.1, 2.35, C.cyan);
  kpi(s, '884', 'Integrated cells', 8.12, 3.1, 2.35, C.cyan);
  panelTitle(s, 'What is ready for review', 5.55, 4.53, 4.6);
  bullets(s, ['Audited multi-source data pipeline', 'VADER, LDA, BERTopic, ABSA, and DistilBERT experiments', 'Chronological model comparison with robustness analysis', 'Two-sided Streamlit dashboard for operations and residents'], 5.55, 4.88, 4.9, 13.3, 0.35);
}

// 3. Problem
{
  const s = baseSlide('Administrative closure does not equal citizen satisfaction', 'Problem and motivation', 3);
  rect(s, 0.75, 1.72, 4.15, 2.7, C.panel, 0.12, C.line);
  addText(s, 'Traditional KPI', 1.02, 2.02, 3.4, 0.3, { fontSize: 19, color: C.cyan, bold: true });
  bullets(s, ['Ticket volume', 'Open-to-close time', 'Backlog and staffing', 'Closed status'], 1.02, 2.55, 3.4, 16, 0.43);
  rect(s, 6.02, 1.72, 4.15, 2.7, C.panel, 0.12, C.line);
  addText(s, 'Citizen reality', 6.29, 2.02, 3.4, 0.3, { fontSize: 19, color: C.amber, bold: true });
  bullets(s, ['Was the issue corrected?', 'Did the request recur?', 'Was communication adequate?', 'Was the work satisfactory?'], 6.29, 2.55, 3.4, 16, 0.43);
  line(s, 4.9, 3.1, 6.02, 3.1, C.cyan, 2.5);
  addText(s, 'gap', 5.18, 2.72, 0.55, 0.24, { fontSize: 15, color: C.cyan, bold: true, align: 'center' });
  addText(s, 'Research opportunity', 0.75, 4.86, 2.5, 0.28, { fontSize: 18, bold: true });
  addText(s, 'Use public survey ground truth and operational narratives to test whether citizen-perceived friction contains incremental predictive information.', 3.15, 4.84, 7.1, 0.5, { fontSize: 15, color: C.muted });
}

// 4. Research design
{
  const s = baseSlide('The study tests predictive value, not causality', 'Research design', 4);
  rect(s, 0.75, 1.62, 11.85, 1.05, C.panel, 0.12, C.line);
  addText(s, 'Research question', 1.05, 1.9, 2.0, 0.25, { fontSize: 16, color: C.cyan, bold: true });
  addText(s, 'Does augmenting structured operational indicators with NLP sentiment, topic, and aspect signals improve out-of-time prediction?', 3.25, 1.84, 8.9, 0.45, { fontSize: 18, bold: true, fontFace: 'Aptos Display' });
  panelTitle(s, 'Hypotheses', 0.75, 3.04, 2.5);
  rect(s, 0.75, 3.45, 5.45, 1.25, C.panel2, 0.12, C.line);
  addText(s, 'H1  |  Delay', 1.05, 3.72, 2.1, 0.25, { fontSize: 18, color: C.green, bold: true });
  addText(s, 'NLP-augmented features improve prediction of resolution delay.', 1.05, 4.1, 4.75, 0.35, { fontSize: 15, color: C.muted });
  rect(s, 6.72, 3.45, 5.45, 1.25, C.panel2, 0.12, C.line);
  addText(s, 'H2  |  Repeat rate', 7.02, 3.72, 2.7, 0.25, { fontSize: 18, color: C.amber, bold: true });
  addText(s, 'NLP-augmented features improve prediction of 14-day repeat requests.', 7.02, 4.1, 4.75, 0.35, { fontSize: 15, color: C.muted });
  addText(s, 'Interpretation rule', 0.75, 5.38, 1.9, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'All findings are aggregate predictive associations at service × borough × month grain.', 2.8, 5.35, 8.8, 0.25, { fontSize: 14, color: C.muted });
}

// 5. Data sources
{
  const s = baseSlide('Two authentic NYC Open Data sources create complementary evidence', 'Data and audit', 5);
  rect(s, 0.75, 1.72, 5.45, 3.15, C.panel, 0.12, C.line);
  addText(s, 'NYC 311 service requests', 1.05, 2.02, 4.4, 0.3, { fontSize: 19, color: C.cyan, bold: true });
  addText(s, 'Socrata ID: erm2-nwe9', 1.05, 2.42, 3.8, 0.2, { fontSize: 11.5, color: C.muted });
  addText(s, '1,199,279 records', 1.05, 2.85, 4.4, 0.4, { fontSize: 25, bold: true, fontFace: 'Aptos Display' });
  bullets(s, ['Operational closure narratives', 'Created and closed timestamps', 'Delay and repeat-request outcomes', 'Top 20 service categories'], 1.05, 3.42, 4.65, 14, 0.34);
  rect(s, 6.72, 1.72, 5.45, 3.15, C.panel, 0.12, C.line);
  addText(s, 'Resolution Satisfaction Survey', 7.02, 2.02, 4.6, 0.3, { fontSize: 19, color: C.amber, bold: true });
  addText(s, 'Socrata ID: 5ijn-vbdv', 7.02, 2.42, 3.8, 0.2, { fontSize: 11.5, color: C.muted });
  addText(s, '406,581 responses', 7.02, 2.85, 4.4, 0.4, { fontSize: 25, bold: true, fontFace: 'Aptos Display' });
  bullets(s, ['5-point satisfaction ground truth', 'Standardized dissatisfaction reasons', 'Borough and month fields', 'Public free-text suppressed for PII'], 7.02, 3.42, 4.65, 14, 0.34);
  addText(s, 'Audit decision', 0.75, 5.35, 1.45, 0.22, { fontSize: 15, color: C.cyan, bold: true });
  addText(s, 'NLP is extracted from NYC 311 resolution narratives; RSAT supplies survey-level labels and satisfaction aggregates.', 2.45, 5.32, 9.6, 0.32, { fontSize: 14, color: C.text });
}

// 6. Integration grain
{
  const s = baseSlide('The join is privacy-safe and the evaluation is chronological', 'Data architecture', 6);
  addText(s, 'Robust cell grain', 0.75, 1.68, 2.6, 0.28, { fontSize: 19, color: C.cyan, bold: true });
  rect(s, 0.75, 2.15, 11.85, 0.85, C.panel, 0.12, C.line);
  addText(s, 'c = (service, borough, year, month)', 1.0, 2.37, 11.35, 0.34, { fontSize: 27, bold: true, fontFace: 'Aptos Display', align: 'center' });
  addText(s, 'No one-to-one survey-to-ticket join is claimed.', 0.75, 3.22, 5.1, 0.25, { fontSize: 14, color: C.muted });
  panelTitle(s, 'Chronological partitions', 0.75, 3.72, 3.3);
  const parts = [
    ['TRAIN', '2023 Jan–Aug', '586 cells', C.cyan],
    ['VALIDATION', '2023 Sep–Dec', '213 cells', C.amber],
    ['OUT-OF-TIME TEST', '2024 horizon', '85 cells', C.green],
  ];
  parts.forEach((p, i) => {
    const x = 0.75 + i * 4.0;
    rect(s, x, 4.2, 3.55, 0.95, C.panel2, 0.12, C.line);
    addText(s, p[0], x + 0.22, 4.38, 2.8, 0.18, { fontSize: 10, color: p[3], bold: true });
    addText(s, p[1], x + 0.22, 4.63, 2.8, 0.22, { fontSize: 17, bold: true });
    addText(s, p[2], x + 0.22, 4.92, 2.8, 0.17, { fontSize: 11.5, color: C.muted });
  });
}

// Keep the intended narrative order inside PptxGenJS itself so the exported
// package remains fully PowerPoint-compatible: cover, story, design, data,
// methods, results, dashboard, implementation, limitations, close.
if (process.env.SKIP_REORDER !== '1') {
  const desiredOrder = [
    ...Array.from({ length: 6 }, (_, i) => i + 12),
    ...Array.from({ length: 8 }, (_, i) => i + 4),
    ...Array.from({ length: 4 }, (_, i) => i),
  ];
  pptx._slides = desiredOrder.map((i) => pptx._slides[i]);
}
if (process.env.SLIDE_LIMIT) {
  pptx._slides = pptx._slides.slice(0, Number(process.env.SLIDE_LIMIT));
}
// Reassign package identifiers after the in-memory reorder so each
// presentation relationship points to the intended slide XML file.
pptx._slides.forEach((slide, i) => {
  slide._rId = i + 2;
  slide._slideNum = i + 1;
  slide._slideId = i + 256;
});

await pptx.writeFile({ fileName: outPath });
console.log(outPath);
