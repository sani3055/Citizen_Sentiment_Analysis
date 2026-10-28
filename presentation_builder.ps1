$ErrorActionPreference = 'Stop'

$root = 'D:\CITY PRJ'
$outputDir = Join-Path $root 'outputs'
$outputPath = Join-Path $outputDir 'Citizen_Sentiment_Analysis_Review2_Final_Review.pptx'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$presentation = $ppt.Presentations.Add()
$presentation.PageSetup.SlideWidth = 960
$presentation.PageSetup.SlideHeight = 540

$C = @{
    bg = 0x20120B
    panel = 0x3A2818
    panel2 = 0x4A3522
    text = 0xF0F6FC
    muted = 0xB8C7D6
    cyan = 0xF0C94C
    teal = 0xB07A2B
    green = 0x88B752
    amber = 0x60BDF6
    red = 0x6C6BFF
    line = 0x523F2D
    white = 0xFFFFFF
}

function Add-Text($slide, [string]$text, [double]$left, [double]$top, [double]$width, [double]$height, [double]$size = 16, [int]$color = 0xF0F6FC, [bool]$bold = $false, [int]$align = 1, [string]$font = 'Aptos') {
    $shape = $slide.Shapes.AddTextbox(1, $left, $top, $width, $height)
    $shape.TextFrame2.TextRange.Text = $text
    $shape.TextFrame2.WordWrap = -1
    $shape.TextFrame2.AutoSize = 0
    $shape.TextFrame2.MarginLeft = 0
    $shape.TextFrame2.MarginRight = 0
    $shape.TextFrame2.MarginTop = 0
    $shape.TextFrame2.MarginBottom = 0
    $shape.TextFrame2.TextRange.Font.Name = $font
    $shape.TextFrame2.TextRange.Font.Size = $size
    $shape.TextFrame2.TextRange.Font.Bold = if ($bold) { -1 } else { 0 }
    $shape.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = $color
    $shape.TextFrame2.TextRange.ParagraphFormat.Alignment = $align
    return $shape
}

function Add-Rect($slide, [double]$left, [double]$top, [double]$width, [double]$height, [int]$fill, [int]$line = -1, [double]$radius = 0) {
    $geo = if ($radius -gt 0) { 5 } else { 1 }
    $shape = $slide.Shapes.AddShape($geo, $left, $top, $width, $height)
    $shape.Fill.ForeColor.RGB = $fill
    $shape.Line.ForeColor.RGB = if ($line -lt 0) { $fill } else { $line }
    $shape.Line.Weight = 0.75
    return $shape
}

function Add-Line($slide, [double]$x1, [double]$y1, [double]$x2, [double]$y2, [int]$color, [double]$weight = 1.5) {
    $line = $slide.Shapes.AddLine($x1, $y1, $x2, $y2)
    $line.Line.ForeColor.RGB = $color
    $line.Line.Weight = $weight
    return $line
}

function Add-Image($slide, [string]$path, [double]$left, [double]$top, [double]$width, [double]$height) {
    if (Test-Path $path) {
        return $slide.Shapes.AddPicture($path, 0, -1, $left, $top, $width, $height)
    }
    Add-Text $slide "Missing figure: $([System.IO.Path]::GetFileName($path))" $left $top $width $height 14 $C.muted $false 2
}

function Add-Footer($slide, [int]$number, [string]$section = 'BCSE316L | Design of Smart Cities') {
    Add-Line $slide 48 508 912 508 $C.line 0.8 | Out-Null
    Add-Text $slide $section 48 516 500 14 9 $C.muted $false 1
    Add-Text $slide ("{0:00}" -f $number) 870 516 42 14 9 $C.muted $false 3
}

function New-Slide([string]$title, [string]$eyebrow, [int]$number) {
    $slide = $presentation.Slides.Add($presentation.Slides.Count + 1, 12)
    $slide.Background.Fill.ForeColor.RGB = $C.bg
    Add-Text $slide $eyebrow.ToUpper() 48 28 700 16 10 $C.cyan $true 1
    Add-Text $slide $title 48 52 860 48 35 $C.text $true 1 'Aptos Display'
    Add-Footer $slide $number
    return $slide
}

function Add-PanelTitle($slide, [string]$title, [double]$left, [double]$top, [double]$width) {
    Add-Text $slide $title $left $top $width 24 20 $C.text $true 1
}

function Add-KPI($slide, [string]$value, [string]$label, [double]$left, [double]$top, [double]$width, [int]$accent = 0xF0C94C) {
    Add-Rect $slide $left $top $width 88 $C.panel $C.line 10 | Out-Null
    Add-Rect $slide $left $top 5 88 $accent $accent 2 | Out-Null
    Add-Text $slide $value ($left + 18) ($top + 14) ($width - 30) 32 25 $C.text $true 1 'Aptos Display'
    Add-Text $slide $label ($left + 18) ($top + 53) ($width - 30) 20 12 $C.muted $false 1
}

function Add-BulletList($slide, [string[]]$items, [double]$left, [double]$top, [double]$width, [double]$height, [double]$size = 16, [int]$color = 0xB8C7D6) {
    $y = $top
    foreach ($item in $items) {
        Add-Text $slide '•' $left $y 16 22 ($size + 2) $C.cyan $true 1
        Add-Text $slide $item ($left + 22) $y ($width - 22) 34 $size $color $false 1
        $y += 40
    }
}

function Add-Table($slide, [string[][]]$rows, [double]$left, [double]$top, [double]$width, [double]$height, [double]$fontSize = 13) {
    $tableShape = $slide.Shapes.AddTable($rows.Count, $rows[0].Count, $left, $top, $width, $height)
    $table = $tableShape.Table
    $rowHeight = $height / $rows.Count
    for ($r = 1; $r -le $rows.Count; $r++) {
        $table.Rows.Item($r).Height = $rowHeight
        for ($c = 1; $c -le $rows[$r-1].Count; $c++) {
            $cell = $table.Cell($r, $c).Shape
            $cell.TextFrame2.TextRange.Text = $rows[$r-1][$c-1]
            $cell.TextFrame2.MarginLeft = 8
            $cell.TextFrame2.MarginRight = 8
            $cell.TextFrame2.MarginTop = 5
            $cell.TextFrame2.MarginBottom = 5
            $cell.TextFrame2.VerticalAnchor = 3
            $cell.TextFrame2.WordWrap = -1
            $cell.TextFrame2.TextRange.Font.Name = 'Aptos'
            $cell.TextFrame2.TextRange.Font.Size = $fontSize
            $cell.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = if ($r -eq 1) { $C.bg } else { $C.text }
            $cell.TextFrame2.TextRange.Font.Bold = if ($r -eq 1) { -1 } else { 0 }
            $cell.Fill.ForeColor.RGB = if ($r -eq 1) { $C.cyan } elseif ($r % 2 -eq 0) { $C.panel } else { $C.panel2 }
            $cell.Line.ForeColor.RGB = $C.line
        }
    }
    return $tableShape
}

$fig = Join-Path $root 'reports\figures'

# 1. Cover
$slide = $presentation.Slides.Add($presentation.Slides.Count + 1, 12)
$slide.Background.Fill.ForeColor.RGB = $C.bg
Add-Rect $slide 0 0 960 14 $C.cyan $C.cyan | Out-Null
Add-Rect $slide 690 0 270 540 $C.panel $C.panel | Out-Null
Add-Rect $slide 690 0 8 540 $C.cyan $C.cyan | Out-Null
Add-Text $slide 'BCSE316L  |  DESIGN OF SMART CITIES' 60 58 560 20 12 $C.cyan $true 1
Add-Text $slide 'Citizen Sentiment Analysis\nof Municipal Services\nUsing Transformer-Based NLP' 60 126 585 180 50 $C.text $true 1 'Aptos Display'
Add-Text $slide 'Review-2 / Final Review Presentation' 62 330 520 30 22 $C.muted $false 1
Add-Text $slide 'Vellore Institute of Technology  •  SCOPE\nGuide: Dr. Kalaavathi B  •  Project / Team 15' 62 390 540 54 16 $C.muted $false 1
Add-Text $slide 'A reproducible civic intelligence pipeline\nfrom open data to decision support' 730 152 180 90 22 $C.text $true 1 'Aptos Display'
Add-Line $slide 730 275 910 275 $C.line 1
Add-Text $slide '1.20M' 730 300 180 34 28 $C.cyan $true 1 'Aptos Display'
Add-Text $slide '311 service requests' 730 338 180 20 13 $C.muted $false 1
Add-Text $slide '406.6K' 730 380 180 34 28 $C.cyan $true 1 'Aptos Display'
Add-Text $slide 'RSAT responses' 730 418 180 20 13 $C.muted $false 1
Add-Text $slide 'October 2026' 60 505 200 14 10 $C.muted $false 1

# 2. Executive story
$slide = New-Slide 'The project turns civic dissatisfaction into measurable operational evidence' 'Executive story' 2
Add-Text $slide 'Core question' 60 124 250 24 22 $C.cyan $true 1
Add-Text $slide 'Does adding sentiment, topic, and grievance signals improve out-of-time prediction of resolution delay and repeat complaints?' 60 158 390 86 24 $C.text $true 1 'Aptos Display'
Add-Text $slide 'The answer is target-specific: the corrected experiment supports a significant delay gain, while repeat-rate improvement remains an observed but uncertain signal.' 60 270 390 70 17 $C.muted $false 1
Add-KPI $slide '+0.0289' 'Delay ΔR² | p = 0.00020' 500 128 190 $C.green
Add-KPI $slide '+0.0257' 'Repeat ΔR² | p = 0.733' 712 128 190 $C.amber
Add-KPI $slide '16 / 16' 'Current automated tests passing' 500 238 190 $C.cyan
Add-KPI $slide '884' 'Integrated service-borough-month cells' 712 238 190 $C.cyan
Add-PanelTitle $slide 'What is ready for review' 500 360 390
Add-BulletList $slide @('Audited multi-source data pipeline', 'VADER, LDA, BERTopic, ABSA, and DistilBERT experiments', 'Chronological model comparison with robustness analysis', 'Two-sided Streamlit dashboard for operations and residents') 500 394 390 110 15 $C.muted

# 3. Problem
$slide = New-Slide 'Administrative closure does not equal citizen satisfaction' 'Problem and motivation' 3
Add-Rect $slide 60 132 370 260 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Traditional KPI' 86 158 280 24 22 $C.cyan $true 1
Add-BulletList $slide @('Ticket volume', 'Open-to-close time', 'Backlog and staffing', 'Closed status') 86 208 300 150 17 $C.text
Add-Rect $slide 530 132 370 260 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Citizen reality' 556 158 280 24 22 $C.amber $true 1
Add-BulletList $slide @('Was the issue corrected?', 'Did the request recur?', 'Was communication adequate?', 'Was the work satisfactory?') 556 208 300 150 17 $C.text
Add-Line $slide 430 262 530 262 $C.cyan 2.5 | Out-Null
Add-Text $slide 'gap' 460 228 42 24 16 $C.cyan $true 2
Add-Text $slide 'Research opportunity' 60 432 260 24 20 $C.text $true 1
Add-Text $slide 'Use public survey ground truth and operational narratives to test whether citizen-perceived friction contains incremental predictive information.' 300 430 600 42 17 $C.muted $false 1

# 4. Research question and hypotheses
$slide = New-Slide 'The study tests incremental predictive value, not causality' 'Research design' 4
Add-Rect $slide 60 128 840 98 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Research question' 84 149 210 22 18 $C.cyan $true 1
Add-Text $slide 'Does augmenting structured operational indicators with NLP sentiment, topic, and aspect signals improve out-of-time prediction?' 300 146 560 48 20 $C.text $true 1 'Aptos Display'
Add-PanelTitle $slide 'Hypotheses' 60 270 280
Add-Rect $slide 60 310 390 100 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'H1  |  Delay' 84 330 140 22 19 $C.green $true 1
Add-Text $slide 'NLP-augmented features improve prediction of resolution delay.' 84 360 330 38 17 $C.muted $false 1
Add-Rect $slide 510 310 390 100 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'H2  |  Repeat rate' 534 330 200 22 19 $C.amber $true 1
Add-Text $slide 'NLP-augmented features improve prediction of 14-day repeat requests.' 534 360 330 38 17 $C.muted $false 1
Add-Text $slide 'Interpretation rule' 60 456 190 20 17 $C.cyan $true 1
Add-Text $slide 'All findings are aggregate predictive associations at service × borough × month grain.' 260 454 640 22 16 $C.muted $false 1

# 5. Data sources
$slide = New-Slide 'Two authentic NYC Open Data sources create complementary evidence' 'Data and audit' 5
Add-Rect $slide 60 130 390 250 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'NYC 311 service requests' 84 154 320 26 22 $C.cyan $true 1
Add-Text $slide 'Socrata ID: erm2-nwe9' 84 190 310 18 13 $C.muted $false 1
Add-Text $slide '1,199,279 records' 84 230 310 34 28 $C.text $true 1 'Aptos Display'
Add-BulletList $slide @('Operational closure narratives', 'Created and closed timestamps', 'Delay and repeat-request outcomes', 'Top 20 service categories') 84 282 320 120 15 $C.muted
Add-Rect $slide 510 130 390 250 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Resolution Satisfaction Survey' 534 154 330 26 22 $C.amber $true 1
Add-Text $slide 'Socrata ID: 5ijn-vbdv' 534 190 310 18 13 $C.muted $false 1
Add-Text $slide '406,581 responses' 534 230 310 34 28 $C.text $true 1 'Aptos Display'
Add-BulletList $slide @('5-point satisfaction ground truth', 'Standardized dissatisfaction reasons', 'Borough and month fields', 'Public free-text suppressed for PII') 534 282 320 120 15 $C.muted
Add-Text $slide 'Audit decision' 60 430 150 22 19 $C.cyan $true 1
Add-Text $slide 'NLP is extracted from NYC 311 resolution narratives; RSAT supplies survey-level labels and satisfaction aggregates.' 220 428 680 42 17 $C.text $false 1

# 6. Integration grain and leakage control
$slide = New-Slide 'The join is privacy-safe and the evaluation is chronological' 'Data architecture' 6
Add-Text $slide 'Robust cell grain' 60 128 250 24 21 $C.cyan $true 1
Add-Rect $slide 60 170 840 80 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'c = (service, borough, year, month)' 96 192 770 36 30 $C.text $true 2 'Aptos Display'
Add-Text $slide 'No one-to-one survey-to-ticket join is claimed.' 60 270 420 22 16 $C.muted $false 1
Add-PanelTitle $slide 'Chronological partitions' 60 326 350
Add-Rect $slide 60 366 240 88 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'TRAIN' 82 382 90 18 12 $C.cyan $true 1
Add-Text $slide '2023 Jan–Aug' 82 410 180 24 20 $C.text $true 1
Add-Text $slide '586 cells' 82 438 160 18 13 $C.muted $false 1
Add-Rect $slide 360 366 240 88 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'VALIDATION' 382 382 130 18 12 $C.amber $true 1
Add-Text $slide '2023 Sep–Dec' 382 410 180 24 20 $C.text $true 1
Add-Text $slide '213 cells' 382 438 160 18 13 $C.muted $false 1
Add-Rect $slide 660 366 240 88 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'OUT-OF-TIME TEST' 682 382 180 18 12 0x88B752 $true 1
Add-Text $slide '2024 horizon' 682 410 180 24 20 $C.text $true 1
Add-Text $slide '85 cells' 682 438 160 18 13 $C.muted $false 1

# 7. EDA and ground truth
$slide = New-Slide 'The survey reveals a strongly negative satisfaction distribution' 'Exploratory findings' 7
Add-Text $slide '62.14%' 60 128 240 50 42 $C.red $true 1 'Aptos Display'
Add-Text $slide 'of validated RSAT responses are dissatisfied' 60 182 290 42 18 $C.text $true 1
Add-Text $slide 'Issue correction is the largest standardized grievance aspect (42.7% of dissatisfied responses).' 60 258 300 70 17 $C.muted $false 1
Add-Rect $slide 400 118 500 260 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'rsat_satisfaction_dist.png') 420 138 460 220 | Out-Null
Add-Text $slide 'RSAT satisfaction distribution' 60 382 300 22 18 $C.cyan $true 1
Add-Text $slide 'This skew establishes a meaningful citizen-distress signal for later aggregation and modeling.' 60 414 780 36 17 $C.muted $false 1

# 8. NLP pipeline
$slide = New-Slide 'The NLP stack progresses from interpretable baselines to domain adaptation' 'NLP methodology' 8
$xs = @(60, 275, 490, 705)
$titles = @('VADER', 'LDA + BERTopic', 'ABSA', 'DistilBERT')
$sub = @('Lexicon sentiment', 'Themes and clusters', 'Six grievance aspects', 'Transformer fine-tuning')
$metrics = @('Accuracy 0.655\nNegative F1 0.800', 'Cᵥ 0.5100\n14 semantic clusters', 'TF-IDF macro-F1 0.1723\nRule baseline 0.1295', 'Test macro-F1 0.3491\nAccuracy 0.4148')
$colors = @($C.cyan, $C.amber, $C.green, $C.red)
for ($i=0; $i -lt 4; $i++) {
    Add-Rect $slide $xs[$i] 155 175 218 $C.panel $C.line 12 | Out-Null
    Add-Rect $slide $xs[$i] 155 175 7 $colors[$i] $colors[$i] 3 | Out-Null
    Add-Text $slide $titles[$i] ($xs[$i] + 22) 180 140 26 22 $C.text $true 1
    Add-Text $slide $sub[$i] ($xs[$i] + 22) 218 140 22 14 $C.muted $false 1
    Add-Text $slide $metrics[$i] ($xs[$i] + 22) 270 140 55 16 $C.text $true 1
}
Add-Line $slide 148 420 812 420 $C.line 1.2 | Out-Null
Add-Text $slide 'Design boundary' 60 444 140 20 16 $C.cyan $true 1
Add-Text $slide 'Resolution narratives are agency text; RSAT provides the citizen-grounded labels and satisfaction aggregates.' 220 442 680 22 16 $C.muted $false 1

# 9. NLP evidence
$slide = New-Slide 'Transformer adaptation materially improves aspect attribution over the classical baseline' 'NLP results' 9
Add-Rect $slide 60 126 420 280 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'absa_per_aspect_f1.png') 78 148 384 230 | Out-Null
Add-Text $slide 'Per-aspect F1 comparison' 78 382 360 18 13 $C.muted $false 1
Add-Rect $slide 520 126 380 280 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Transformer run' 548 154 280 24 22 $C.cyan $true 1
Add-KPI $slide '0.3491' 'Out-of-time macro-F1' 548 204 300 $C.green
Add-KPI $slide '+0.1768' 'Macro-F1 gain vs TF-IDF' 548 304 300 $C.amber
Add-Text $slide 'Kaggle Tesla T4 • 3 epochs • 2e-5 learning rate\n41,746 chronological examples across train / validation / test' 548 420 310 42 14 $C.muted $false 1

# 10. Outcomes
$slide = New-Slide 'Operational outcomes quantify both delay and recurring demand' 'Operational outcomes' 10
Add-KPI $slide '2.90 h' 'Median raw resolution delay' 60 126 200 $C.cyan
Add-KPI $slide '91.11 h' 'Mean winsorized delay' 280 126 200 $C.amber
Add-KPI $slide '44.88%' '14-day repeat rate' 500 126 200 $C.red
Add-KPI $slide '50.52%' '30-day repeat rate' 720 126 180 $C.green
Add-Rect $slide 60 252 420 210 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'nyc311_delay_hist.png') 78 270 384 170 | Out-Null
Add-Text $slide 'Delay distribution is highly right-skewed; p99 winsorization cutoff = 2,454.96 hours.' 78 442 380 28 13 $C.muted $false 1
Add-Rect $slide 520 252 380 210 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'nyc311_monthly_volume.png') 538 270 344 170 | Out-Null
Add-Text $slide 'Repeat rates rise with longer observation windows: 39.10% at 7 days → 50.52% at 30 days.' 538 442 344 28 13 $C.muted $false 1

# 11. Modeling design
$slide = New-Slide 'The predictive experiment isolates the incremental role of NLP features' 'Predictive modeling' 11
Add-Text $slide 'Structured baseline' 60 132 270 22 21 $C.cyan $true 1
Add-BulletList $slide @('Service identity', 'Borough', 'Month seasonality', 'Request volume') 60 174 280 140 17 $C.muted
Add-Text $slide '→' 370 222 60 40 34 $C.cyan $true 2
Add-Text $slide 'NLP-augmented model' 500 132 300 22 21 $C.amber $true 1
Add-BulletList $slide @('All baseline features', 'VADER sentiment rates', 'LDA / BERTopic features', 'ABSA aspect proportions', 'RSAT satisfaction signals') 500 174 340 180 17 $C.muted
Add-PanelTitle $slide 'Evaluation protocol' 60 386 250
Add-Rect $slide 60 424 840 48 $C.panel $C.line 10 | Out-Null
Add-Text $slide 'Ridge  •  Random Forest  •  LightGBM     |     validation-selected algorithm     |     one untouched 2024 horizon test' 84 438 790 20 15 $C.text $true 2

# 12. Main model results
$slide = New-Slide 'NLP adds a modest but statistically significant gain for delay; repeat-rate evidence is inconclusive' 'Main results' 12
Add-Rect $slide 60 120 390 300 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'model_r2_comparison.png') 80 145 350 235 | Out-Null
Add-Text $slide '2024 out-of-time R² comparison' 80 392 330 18 13 $C.muted $false 1
$rows = @(
    @('Target', 'Model', 'Base R²', 'Aug R²', 'ΔR²', 'p-value'),
    @('Delay (h)', 'LightGBM', '0.5149', '0.5438', '+0.0289', '0.00020'),
    @('Repeat 14d', 'LightGBM', '0.7184', '0.7441', '+0.0257', '0.733')
)
Add-Table $slide $rows 480 142 420 155 12 | Out-Null
Add-Rect $slide 480 330 420 90 $C.panel2 $C.line 10 | Out-Null
Add-Text $slide 'Interpretation' 502 348 120 20 17 $C.cyan $true 1
Add-Text $slide 'Delay: confirmed incremental predictive association.\nRepeat: positive observed gain, but not statistically significant.' 502 378 370 36 15 $C.text $false 1

# 13. Robustness
$slide = New-Slide 'Robustness analysis strengthens the delay result and qualifies the repeat-rate result' 'Uncertainty analysis' 13
Add-Rect $slide 60 122 470 300 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'robustness_delta_r2.png') 78 145 434 235 | Out-Null
Add-Text $slide 'Five seeds + 2,000 bootstrap resamples' 78 392 420 18 13 $C.muted $false 1
Add-Rect $slide 570 122 330 300 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Delay' 596 150 120 22 21 $C.green $true 1
Add-Text $slide 'Mean ΔR²  +0.1287 ± 0.0097\n95% bootstrap CI  [+0.0499, +0.2259]' 596 190 270 54 18 $C.text $true 1
Add-Line $slide 596 264 872 264 $C.line 1 | Out-Null
Add-Text $slide 'Repeat rate' 596 292 180 22 21 $C.amber $true 1
Add-Text $slide 'Mean ΔR²  +0.0403 ± 0.0072\n95% bootstrap CI  [-0.0072, +0.0794]' 596 332 270 54 18 $C.text $true 1
Add-Text $slide 'The interval crossing zero is the key qualification.' 596 398 270 36 14 $C.muted $false 1

# 14. Explainability
$slide = New-Slide 'Explainability links the prediction to operational, thematic, and sentiment signals' 'Model interpretation' 14
Add-Rect $slide 60 122 510 330 $C.panel $C.line 12 | Out-Null
Add-Image $slide (Join-Path $fig 'shap_feature_importance.png') 78 145 474 270 | Out-Null
Add-Text $slide 'Global SHAP feature ranking' 78 424 400 18 13 $C.muted $false 1
Add-Text $slide 'Top contributors in the augmented delay model' 620 136 270 24 21 $C.cyan $true 1
Add-BulletList $slide @('log_request_volume', 'topic_entropy', 'response-time aspect', 'month seasonality', 'VADER negative rate') 620 182 250 150 17 $C.text
Add-Text $slide 'Meaning' 620 364 120 22 18 $C.amber $true 1
Add-Text $slide 'The model uses both operational pressure and civic-language signals; the dashboard exposes these signals for review rather than hiding them behind a single score.' 620 398 250 58 16 $C.muted $false 1

# 15. Dashboard
$slide = New-Slide 'The final system turns the analysis into two decision-support views' 'Interactive dashboard' 15
Add-Rect $slide 60 128 390 290 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Municipal Operations' 86 154 300 26 22 $C.cyan $true 1
Add-BulletList $slide @('Filter by borough, service, and period', 'Priority queue with risk score', 'Trend and borough comparison charts', 'Model evidence and SHAP view', 'Downloadable priority queue') 86 204 320 190 16 $C.text
Add-Rect $slide 510 128 390 290 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Resident View' 536 154 300 26 22 $C.amber $true 1
Add-BulletList $slide @('Plain-language KPI summary', 'Historical delay and repeat trends', 'Citywide service comparison', 'Privacy-safe aggregate values', 'No names, addresses, or ticket text') 536 204 320 190 16 $C.text
Add-Text $slide 'Live local link' 60 454 130 20 16 $C.cyan $true 1
Add-Text $slide 'http://localhost:8501' 210 450 320 28 21 $C.text $true 1 'Aptos Display'
Add-Text $slide 'Data grain: service × borough × month' 600 454 300 22 16 $C.muted $false 3

# 16. Reproducibility and implementation
$slide = New-Slide 'All major pipeline phases are implemented with inspectable artifacts' 'Implementation status' 16
Add-Text $slide 'Completed pipeline' 60 124 240 24 21 $C.cyan $true 1
$phaseLabels = @('Audit', 'Environment', 'Ingestion', 'EDA', 'NLP', 'Outcomes', 'Integration', 'Modeling', 'Transformer', 'Dashboard', 'Tests', 'Report')
$phaseColors = @($C.green,$C.green,$C.green,$C.green,$C.cyan,$C.cyan,$C.cyan,$C.amber,$C.amber,$C.red,$C.green,$C.green)
for ($i=0; $i -lt $phaseLabels.Count; $i++) {
    $col = $i % 6
    $row = [math]::Floor($i / 6)
    $x = 60 + ($col * 145)
    $y = 170 + ($row * 78)
    Add-Rect $slide $x $y 125 50 $C.panel $C.line 8 | Out-Null
    Add-Rect $slide $x $y 6 50 $phaseColors[$i] $phaseColors[$i] 2 | Out-Null
    Add-Text $slide ("{0:00}" -f ($i + 1)) ($x + 16) ($y + 8) 28 16 11 $C.muted $true 1
    Add-Text $slide $phaseLabels[$i] ($x + 16) ($y + 25) 100 18 14 $C.text $true 1
}
Add-PanelTitle $slide 'Current verification' 60 350 240
Add-KPI $slide '16 / 16' 'pytest checks passing' 60 388 210 $C.green
Add-KPI $slide '108' 'environment dependencies verified' 290 388 250 $C.cyan
Add-KPI $slide '2024' 'operational out-of-time horizon' 560 388 230 $C.amber

# 17. Limitations and next steps
$slide = New-Slide 'The project is submission-ready when its boundaries are stated clearly' 'Limitations and next steps' 17
Add-Rect $slide 60 126 390 300 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'What the evidence does not claim' 84 152 320 24 21 $C.red $true 1
Add-BulletList $slide @('No causal effect is established.', 'RSAT free-text comments are PII-suppressed.', 'ABSA is a domain-transfer evaluation.', 'Repeat-rate gain is not significant.', '2024 is the local operational test horizon.') 84 198 320 190 16 $C.text
Add-Rect $slide 510 126 390 300 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Highest-value next steps' 534 152 320 24 21 $C.green $true 1
Add-BulletList $slide @('Complete two-annotator 311 ABSA sample.', 'Report Cohen’s kappa and human macro-F1.', 'Collect a longer out-of-time horizon.', 'Validate transfer on another 311 city.', 'Monitor drift before operational deployment.') 534 198 320 190 16 $C.text
Add-Text $slide 'Academic position' 60 456 160 20 17 $C.cyan $true 1
Add-Text $slide 'Strong end-to-end engineering and reproducibility; conclusions are calibrated to the available evidence.' 240 454 660 24 16 $C.muted $false 1

# 18. Close
$slide = $presentation.Slides.Add($presentation.Slides.Count + 1, 12)
$slide.Background.Fill.ForeColor.RGB = $C.bg
Add-Rect $slide 60 76 8 370 $C.cyan $C.cyan | Out-Null
Add-Text $slide 'Final takeaway' 110 92 300 24 14 $C.cyan $true 1
Add-Text $slide 'Municipal service quality is more than closure speed.' 110 142 700 72 40 $C.text $true 1 'Aptos Display'
Add-Text $slide 'This project demonstrates a reproducible way to connect citizen dissatisfaction, civic text signals, and operational outcomes — with transparent limits and an actionable dashboard.' 110 250 700 80 22 $C.muted $false 1
Add-Rect $slide 110 374 720 74 $C.panel $C.line 12 | Out-Null
Add-Text $slide 'Key result' 136 394 120 20 16 $C.cyan $true 1
Add-Text $slide 'Significant incremental evidence for resolution-delay prediction; repeat-rate evidence remains a research opportunity.' 270 388 525 34 18 $C.text $true 1
Add-Text $slide 'Thank you  •  Questions and discussion' 110 492 500 18 15 $C.muted $false 1
Add-Text $slide '18' 870 492 40 18 11 $C.muted $false 3

# Fix accidental literal newline escape sequences for text boxes.
foreach ($shape in $presentation.Slides | ForEach-Object { $_.Shapes }) {
    try {
        $txt = $shape.TextFrame2.TextRange.Text
        if ($txt -and $txt.Contains('\n')) {
            $shape.TextFrame2.TextRange.Text = $txt.Replace('\n', "`n")
        }
    } catch { }
}

$presentation.SaveAs($outputPath, 24)
$presentation.Close()
$ppt.Quit()
Write-Output $outputPath
