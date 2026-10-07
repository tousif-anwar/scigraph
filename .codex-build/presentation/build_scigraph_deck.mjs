import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "C:/Users/tousi/Documents/ta_a5/Common/scigraph";
const SKILL_DIR = "C:/Users/tousi/.codex/plugins/cache/openai-primary-runtime/presentations/26.915.20218/skills/presentations";
const TMP_DIR = path.join(workspaceDir, ".codex-build", "presentation");
const FINAL_PPTX = path.join(workspaceDir, "deliverables", "SciGraph_Project_Presentation_v2.pptx");
const RUNTIME_PYTHON = "C:/Users/tousi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";

const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href,
);

await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const fontFamily = resolvePresentationFont();

const W = 1280;
const H = 720;
const C = {
  navy: "#0B1F33",
  ink: "#14212B",
  muted: "#5E6B78",
  teal: "#118C8B",
  green: "#4E9A51",
  gold: "#C58A25",
  red: "#B9483D",
  blue: "#2F6FBB",
  pale: "#F4F7FA",
  line: "#D8E0E8",
  white: "#FFFFFF",
};

function readJson(rel) {
  return JSON.parse(awaitableText(path.join(workspaceDir, rel)));
}

function awaitableText(file) {
  return fs.readFile(file, "utf-8");
}

async function loadJson(rel) {
  return JSON.parse(await fs.readFile(path.join(workspaceDir, rel), "utf-8"));
}

function sourceNote(...sources) {
  return `Sources: ${sources.join("; ")}. Metrics reflect the completed 2,500-record development run, not the in-progress 1,000,000-record production acquisition.`;
}

function addBg(slide) {
  slide.background.fill = C.white;
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: 0, width: W, height: 18 },
    fill: C.teal,
    line: { fill: "none", width: 0 },
  });
  slide.shapes.add({
    geometry: "rect",
    position: { left: 0, top: H - 18, width: W, height: 18 },
    fill: C.navy,
    line: { fill: "none", width: 0 },
  });
}

function addTitle(slide, title, subtitle = "") {
  const t = slide.shapes.add({
    geometry: "textbox",
    position: { left: 64, top: 44, width: 900, height: 52 },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  t.text = title;
  t.text.style = {
    typeface: fontFamily,
    fontSize: 31,
    bold: true,
    color: C.navy,
    autoFit: "shrinkText",
  };
  if (subtitle) {
    const s = slide.shapes.add({
      geometry: "textbox",
      position: { left: 66, top: 94, width: 880, height: 32 },
      fill: "none",
      line: { fill: "none", width: 0 },
    });
    s.text = subtitle;
    s.text.style = {
      typeface: fontFamily,
      fontSize: 15,
      color: C.muted,
      autoFit: "shrinkText",
    };
  }
}

function addText(slide, text, x, y, w, h, opts = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: fontFamily,
    fontSize: opts.size ?? 17,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    autoFit: "shrinkText",
  };
  return box;
}

function addMetric(slide, label, value, x, y, color = C.teal) {
  const v = addText(slide, value, x, y, 210, 52, { size: 33, bold: true, color });
  const l = addText(slide, label, x, y + 48, 230, 44, { size: 14, color: C.muted });
  return { v, l };
}

async function addImage(slide, relPath, alt, x, y, w, h) {
  const bytes = await fs.readFile(path.join(workspaceDir, relPath));
  slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left: x, top: y, width: w, height: h },
  });
}

function styleTable(table) {
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  for (let c = 0; c < table.columns.length; c += 1) {
    const cell = table.getCell(0, c);
    cell.fill = C.navy;
    cell.text.style = { typeface: fontFamily, fontSize: 14, bold: true, color: C.white };
  }
  for (let r = 1; r < table.rows.length; r += 1) {
    for (let c = 0; c < table.columns.length; c += 1) {
      table.getCell(r, c).text.style = { typeface: fontFamily, fontSize: 13, color: C.ink };
    }
  }
}

const schema = await loadJson("reports/results/schema_summary.json");
const pipeline = await loadJson("reports/results/bronze_silver_gold_report.json");
const text = await loadJson("reports/results/text_analysis_report.json");
const cluster = await loadJson("reports/results/clustering_report.json");
const citation = await loadJson("reports/results/citation_graph_report.json");
const author = await loadJson("reports/results/author_collaboration_report.json");
const temporal = await loadJson("reports/results/temporal_analysis_report.json");
const streaming = await loadJson("reports/results/streaming_simulation_report.json");
const sparse = await loadJson("reports/results/retrieval_report.json");
const advanced = await loadJson("reports/results/advanced_retrieval_results.json");
const ml = await loadJson("reports/results/ml_citation_prediction_report.json");
const feature = await loadJson("reports/results/feature_mart_report.json");

const stats = schema.dataset_statistics;
const stages = pipeline.stage_counts;
const bestSystem = [...advanced.systems].sort((a, b) => b.ndcg_at_k - a.ndcg_at_k)[0];

const presentation = Presentation.create({ slideSize: { width: W, height: H } });
const slides = [];

// 1
{
  const slide = presentation.slides.add();
  slides.push(slide);
  slide.background.fill = C.navy;
  slide.shapes.add({ geometry: "rect", position: { left: 0, top: H - 105, width: W, height: 105 }, fill: C.teal, line: { fill: "none", width: 0 } });
  addText(slide, "SciGraph", 72, 96, 760, 80, { size: 52, bold: true, color: C.white });
  addText(slide, "Scalable scientific literature intelligence over OpenAlex metadata", 76, 176, 820, 52, { size: 24, color: "#CFE6E6" });
  addText(slide, "A reproducible Spark pipeline with text, graph, temporal, retrieval, ML, ranking, and visualization outputs.", 76, 270, 760, 86, { size: 20, color: C.white });
  addMetric(slide, "OpenAlex article records", "2,500", 78, 458, C.white);
  addMetric(slide, "Gold citation edges", "53,877", 328, 458, C.white);
  addMetric(slide, "Generated figures", "13", 578, 458, C.white);
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/schema_summary.json", "reports/results/bronze_silver_gold_report.json", "docs/VISUALIZATIONS.md"));
}

// 2
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Project Objective", "Build a transparent literature analytics system without relying on an LLM-only workflow");
  addText(slide, "The project turns raw scholarly metadata into analysis-ready tables, reports, and visual evidence. The emphasis is on reproducibility, measured results, and clear limitations.", 74, 150, 520, 126, { size: 22, color: C.ink });
  const bullets = [
    "Acquire OpenAlex article records with abstracts",
    "Normalize nested metadata with Spark",
    "Analyze text, citation links, collaboration, and time",
    "Compare sparse, dense, hybrid, and graph-aware retrieval",
    "Publish a feature mart, figures, notebook, and final report",
  ];
  bullets.forEach((b, i) => addText(slide, `${i + 1}. ${b}`, 112, 326 + i * 46, 650, 34, { size: 20, color: C.ink }));
  await addImage(slide, "reports/figures/feature_mart_availability.png", "Feature mart availability chart", 760, 154, 430, 360);
  slide.speakerNotes.textFrame.setText(sourceNote("docs/PROJECT_REPORT.md", "reports/figures/feature_mart_availability.png"));
}

// 3
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "System Architecture", "A layered pipeline keeps raw data, normalized tables, and analysis outputs separate");
  const boxes = [
    ["OpenAlex API", "Raw JSONL metadata", 58],
    ["Bronze", "Raw nested Spark table", 238],
    ["Silver", "Publication-level normalization", 418],
    ["Gold", "Publications, authors, citations, topics", 598],
    ["Analysis", "Text, graph, temporal, retrieval, ML", 778],
    ["Outputs", "Reports, figures, tables, notebook", 958],
  ];
  boxes.forEach(([head, body, x], i) => {
    slide.shapes.add({ geometry: "roundRect", position: { left: x, top: 220, width: 160, height: 155 }, fill: i % 2 === 0 ? "#EAF6F6" : "#F5F0E8", line: { fill: C.line, width: 1 } });
    addText(slide, head, x + 14, 242, 130, 34, { size: 19, bold: true, color: C.navy });
    addText(slide, body, x + 14, 292, 128, 62, { size: 14, color: C.ink });
    if (i < boxes.length - 1) {
      slide.shapes.add({ geometry: "rightArrow", position: { left: x + 162, top: 272, width: 54, height: 46 }, fill: C.teal, line: { fill: "none", width: 0 } });
    }
  });
  addText(slide, "Storage pattern: Parquet tables for data, JSON for metrics, Markdown for interpretation, PNG for figures.", 112, 470, 980, 54, { size: 20, color: C.ink });
  slide.speakerNotes.textFrame.setText(sourceNote("docs/ARCHITECTURE.md", "docs/PROJECT_REPORT.md"));
}

// 4
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Dataset And Scale", "The completed run uses a larger 2,500-record sample");
  const table = slide.tables.add({
    rows: 6,
    columns: 2,
    left: 70,
    top: 150,
    width: 470,
    height: 310,
    values: [
      ["Metric", "Value"],
      ["Records", stats.record_count],
      ["Publication years", `${stats.date_range_publication_year[0]}-${stats.date_range_publication_year[1]}`],
      ["Unique authors", stats.unique_authors],
      ["Referenced works observed", stats.reference_count],
      ["Document type", "article"],
    ],
  });
  styleTable(table);
  await addImage(slide, "reports/figures/dataset_publications_by_year.png", "Publications by year", 620, 135, 540, 380);
  addText(slide, "The sample remains heterogeneous, which helps test the pipeline but weakens claims about field-specific clusters.", 84, 558, 980, 48, { size: 18, color: C.muted });
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/schema_summary.json", "reports/figures/dataset_publications_by_year.png"));
}

// 5
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Data Quality And Spark Outputs", "No blocking quality errors appeared in the completed run");
  addMetric(slide, "Gold publications", String(stages.gold_publications), 74, 152, C.teal);
  addMetric(slide, "Gold authors", String(stages.gold_authors), 316, 152, C.blue);
  addMetric(slide, "Citation edges", String(stages.gold_citation_edges), 558, 152, C.gold);
  await addImage(slide, "reports/figures/data_quality_checks.png", "Data quality checks", 92, 292, 455, 300);
  await addImage(slide, "reports/figures/pipeline_stage_counts.png", "Pipeline stage counts", 654, 292, 455, 300);
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/data_quality_report.json", "reports/results/bronze_silver_gold_report.json", "reports/figures/data_quality_checks.png", "reports/figures/pipeline_stage_counts.png"));
}

// 6
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Text Analysis And Clustering", "Text features scale, but clusters remain exploratory");
  addMetric(slide, "English text documents", String(text.document_count), 72, 142, C.teal);
  addMetric(slide, "Retained vocabulary", String(text.vocabulary_size), 340, 142, C.blue);
  addMetric(slide, "Selected K", String(cluster.selected_k), 608, 142, C.gold);
  await addImage(slide, "reports/figures/text_top_terms.png", "Top text terms", 72, 288, 500, 300);
  await addImage(slide, "reports/figures/clustering_results.png", "Clustering results", 646, 288, 500, 300);
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/text_analysis_report.json", "reports/results/clustering_report.json", "reports/figures/text_top_terms.png", "reports/figures/clustering_results.png"));
}

// 7
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Graph And Temporal Signals", "Collaboration is informative, while sampled citation links remain sparse");
  addText(slide, `Citation graph: ${citation.full_edge_count.toLocaleString()} full edges, but ${citation.in_sample_edge_count} in-sample citation edges. PageRank is therefore limited for ranking sampled papers.`, 74, 142, 500, 78, { size: 18, color: C.ink });
  addText(slide, `Author graph: ${author.author_count.toLocaleString()} authors and ${author.collaboration_edge_count.toLocaleString()} coauthor edges across the current sample.`, 74, 238, 500, 64, { size: 18, color: C.ink });
  addText(slide, `Temporal analysis: ${temporal.year_bucket_count} year buckets and ${temporal.topic_year_row_count.toLocaleString()} topic-year rows.`, 74, 320, 500, 58, { size: 18, color: C.ink });
  await addImage(slide, "reports/figures/author_collaboration_summary.png", "Author collaboration summary", 650, 126, 455, 235);
  await addImage(slide, "reports/figures/temporal_yearly_metrics.png", "Temporal yearly metrics", 650, 382, 455, 210);
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/citation_graph_report.json", "reports/results/author_collaboration_report.json", "reports/results/temporal_analysis_report.json"));
}

// 8
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Retrieval And ML Results", "Graph-aware reranking produced the strongest NDCG in the current comparison");
  const table = slide.tables.add({
    rows: 6,
    columns: 5,
    left: 58,
    top: 138,
    width: 700,
    height: 305,
    values: [
      ["System", "P@10", "Recall@10", "MRR", "NDCG@10"],
      ...advanced.systems
        .filter((r) => ["bm25", "dense", "hybrid_rrf", "hybrid_reranked", "hybrid_reranked_graph"].includes(r.system))
        .map((r) => [
          r.system.replaceAll("_", " "),
          r.precision_at_k.toFixed(2),
          r.recall_at_k.toFixed(2),
          r.mrr.toFixed(2),
          r.ndcg_at_k.toFixed(2),
        ]),
    ],
  });
  styleTable(table);
  addMetric(slide, "Best NDCG@10", bestSystem.ndcg_at_k.toFixed(4), 825, 150, C.teal);
  addMetric(slide, "Sparse P@10", sparse.mean_precision_at_k.toFixed(2), 825, 282, C.blue);
  addMetric(slide, "Citation model AUC", ml.area_under_roc.toFixed(4), 825, 414, C.gold);
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/retrieval_report.json", "reports/results/advanced_retrieval_results.json", "reports/results/ml_citation_prediction_report.json"));
}

// 9
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Feature Mart And Review Artifacts", "The project now has a single inspection surface plus presentation-ready outputs");
  addText(slide, `The feature mart preserves ${feature.publication_rows.toLocaleString()} publication rows and ${feature.feature_columns} columns. Text-derived features cover ${(feature.text_feature_availability * 100).toFixed(1)}% of rows, while ranking features cover ${(feature.ranking_availability * 100).toFixed(1)}%.`, 70, 146, 520, 92, { size: 20, color: C.ink });
  await addImage(slide, "reports/figures/feature_mart_availability.png", "Feature mart availability", 670, 126, 430, 245);
  await addImage(slide, "reports/figures/ranking_top_publications.png", "Top ranked publications", 670, 394, 430, 210);
  addText(slide, "Review paths: PROJECT_REPORT.md, VISUALIZATIONS.md, reports/tables CSV files, and notebooks/scigraph_visual_summary.ipynb.", 84, 524, 820, 48, { size: 18, color: C.muted });
  slide.speakerNotes.textFrame.setText(sourceNote("reports/results/feature_mart_report.json", "docs/PROJECT_REPORT.md", "docs/VISUALIZATIONS.md"));
}

// 10
{
  const slide = presentation.slides.add();
  slides.push(slide);
  addBg(slide);
  addTitle(slide, "Limitations And Next Steps", "The strongest deliverable is the reproducible system and its measured evidence");
  const left = [
    ["Current limitation", "Why it matters"],
    ["Heterogeneous sample", "Clusters do not represent validated research fields"],
    ["No in-sample citation edges", "PageRank has limited value for sampled-paper ranking"],
    ["Proxy retrieval labels", "Metrics need human judgments for stronger claims"],
    ["Static streaming replay", "Production streaming would need checkpointed inputs"],
  ];
  const table = slide.tables.add({ rows: left.length, columns: 2, left: 70, top: 145, width: 690, height: 330, values: left });
  styleTable(table);
  addText(slide, "Recommended extensions", 835, 148, 300, 32, { size: 22, bold: true, color: C.navy });
  [
    "Acquire a field-specific or citation-neighborhood sample",
    "Add human relevance judgments for retrieval",
    "Build a semantic index with FAISS or Chroma",
    "Turn the notebook into an interactive dashboard",
  ].forEach((item, i) => addText(slide, `${i + 1}. ${item}`, 835, 196 + i * 66, 320, 46, { size: 17, color: C.ink }));
  slide.speakerNotes.textFrame.setText(sourceNote("docs/LIMITATIONS.md", "docs/PROJECT_REPORT.md"));
}

const previewDir = path.join(TMP_DIR, "previews");
await fs.mkdir(previewDir, { recursive: true });
for (let i = 0; i < slides.length; i += 1) {
  const slide = slides[i];
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${String(i + 1).padStart(2, "0")}.png`), new Uint8Array(await png.arrayBuffer()));
}

const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "scigraph_candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const requirements = {
  explicitTotalSlideCount: 10,
  requiredNativeTableOwnerSlides: [4, 8, 10],
  requiredNativeChartOwnerSlides: [],
};
const fontPolicy = { basis: "design", families: Array.from(new Set([fontFamily, "Calibri"])) };

await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide",
    "4",
    "--require-native-table-slide",
    "8",
    "--require-native-table-slide",
    "10",
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "SciGraph_Project_Presentation_v2.validation.json"),
});

console.log(JSON.stringify({ final: FINAL_PPTX, previews: previewDir, fontFamily }, null, 2));
