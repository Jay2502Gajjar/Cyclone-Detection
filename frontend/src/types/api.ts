/**
 * The API contract, in TypeScript.
 *
 * API_CONTRACT.md expresses the contract once, as these types. Java records and Pydantic
 * models mirror them. Three services written against one contract in three languages
 * will drift unless something checks, so `tsc` on this file is the frontend's half of
 * that check: if the backend changes a field, the build fails here rather than the UI
 * quietly rendering `undefined` during a demo.
 */

// --- provenance -----------------------------------------------------------------

/** Where a value came from. See docs/provenance.md. */
export type Provenance =
  | 'OBSERVED'
  | 'TRAINED_MODEL'
  | 'DERIVED_MEASUREMENT'
  | 'STATISTICAL_BASELINE'
  | 'ANALOGUE_ENSEMBLE'
  | 'RULE_ENGINE'
  | 'LLM_NARRATION'
  | 'DEMO_DATA'

/** A held-out metric and the baseline it is compared against. Both halves required. */
export interface MetricInfo {
  name: string
  value: number
  baseline?: string | null
  baselineValue?: number | null
  n?: number | null
}

/** The provenance stamp attached to every analysis block. */
export interface Source {
  provenance: Provenance
  model?: string | null
  version?: string | null
  isTrained?: boolean | null
  metric?: MetricInfo | null
}

export interface ApiError {
  code: string
  message: string
  detail?: string | null
}

// --- health ----------------------------------------------------------------------

export interface ModelInfo {
  key: string
  version: string
  provenance: Provenance
  isTrained: boolean
}

export interface HealthResponse {
  status: 'UP' | 'DEGRADED'
  aiService: { status: 'UP' | 'DOWN'; models: ModelInfo[] }
  database: 'UP' | 'DOWN'
  demoMode: boolean
  bundleVersion: string
}

// --- storms ----------------------------------------------------------------------

export interface StormSummary {
  sid: string
  name: string
  basin: string
  seasonYear: number
  startTime: string
  endTime: string
  peakVmaxKt: number | null
  peakCategory: string | null
  frameCount: number
  framesWithImagery: number
  isDemo: boolean
  split: 'train' | 'val' | 'test'
}

export interface Landfall {
  time: string
  lat: number
  lon: number
  place: string | null
}

/**
 * One point on the scrubber. Deliberately thin: a whole storm's worth of these arrives
 * in the storm-detail call, so dragging the timeline touches no network at all.
 */
export interface TrackFrame {
  t: string
  lat: number
  lon: number
  vmaxKt: number | null
  pressureHpa: number | null
  category: string | null
  imageUrl: string | null
  hasAnalysis: boolean
  /** The CNN's per-frame estimate — the dashed line on the sparkline. */
  cnnVmaxKt: number | null
  regime: string | null
}

export interface StormDetail extends StormSummary {
  landfall: Landfall | null
  frames: TrackFrame[]
  sources: Record<string, Source>
}

// --- frame analysis ---------------------------------------------------------------

export interface ObservedBlock {
  lat: number
  lon: number
  vmaxKt: number | null
  pressureHpa: number | null
  category: string | null
  distToCoastKm: number | null
  source: Source
}

/**
 * Two provenance stamps, not one. The measurements are deterministic physics over the
 * raw brightness-temperature field; the regime label is a rule engine's reading of them.
 * Merging the stamps would let a hand-written threshold borrow a measurement's standing.
 */
export interface StructureBlock {
  regime: string | null
  regimeLabel: string | null
  eyePresent: boolean | null
  eyeRadiusKm: number | null
  eyeRingBtContrastK: number | null
  minBtK: number | null
  cdoFraction100km: number | null
  axisymmetry: number | null
  convectiveRingRadiusKm: number | null
  coldCloudOffsetKm: number | null
  rulesApplied: string[]
  metricsSource: Source
  regimeSource: Source
}

export interface VisionBlock {
  vmaxKt: number | null
  category: string | null
  confidence: number | null
  gradcamUrl: string | null
  source: Source
}

export interface FrameAnalysis {
  sid: string
  t: string
  observed: ObservedBlock
  imageUrl: string | null
  imageTime: string | null
  imageSource: string | null
  structure: StructureBlock
  vision: VisionBlock
  analysisVersion: string | null
}

// --- forecast ---------------------------------------------------------------------

export interface ShapFactor {
  feature: string
  shap: number
  direction: 'increases' | 'decreases'
}

export interface IntensityForecast {
  deltaVmax24hKt: number | null
  predictedVmax24hKt: number | null
  trend: 'INTENSIFYING' | 'WEAKENING' | 'STEADY' | null
  confidence: number | null
  riProbability: number | null
  /** Travels with riProbability: 34% means nothing without the ~5% base rate. */
  riBaseRate: number | null
  topFactors: ShapFactor[]
  source: Source
}

export interface TrackPoint {
  leadHours: 12 | 24 | 48
  lat: number
  lon: number
  coneRadiusP67Km: number | null
  coneRadiusP90Km: number | null
  predictedVmaxKt: number | null
}

export interface TrackForecast {
  points: TrackPoint[]
  source: Source
  /** The cone is a percentile of held-out error, not a model output. */
  coneSource: Source
  coneBasis: string
}

export interface AnalogueOutcome {
  intensifiedCount: number
  weakenedCount: number
  meanDeltaVmax24hKt: number | null
  riCount: number
  riFraction: number | null
  riBaseRate: number | null
}

export interface AnalogueMatch {
  rank: number
  sid: string
  name: string
  time: string
  similarity: number
  outcomeDeltaVmax24hKt: number | null
  wasRi: boolean | null
  onwardTrack: number[][]
}

export interface AnalogueBlock {
  k: number
  outcome: AnalogueOutcome
  matches: AnalogueMatch[]
  exclusions: string[]
  source: Source
}

export interface RiskBlock {
  score: number | null
  level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | null
  formula: string | null
  terms: Record<string, number>
  nearestCoast: string | null
  landfallWindowHours: number | null
  source: Source
}

export interface ReportBlock {
  text: string
  source: Source
}

/** Assembled by the backend from the database. The AI service never produces it. */
export interface VerificationBlock {
  available: boolean
  observedAt24h: { t: string; lat: number; lon: number; vmaxKt: number | null } | null
  observedAt48h: { t: string; lat: number; lon: number; vmaxKt: number | null } | null
  trackErrorKm24h: number | null
  trackErrorKm48h: number | null
  intensityErrorKt24h: number | null
  insideConeP67: boolean | null
  insideConeP90: boolean | null
  riOccurred: boolean | null
  riWarningIssued: boolean | null
  source: Source
}

export interface ForecastResponse {
  sid: string
  issuedFor: string
  modelBundleVersion: string
  current: ObservedBlock
  structure: StructureBlock
  vision: VisionBlock
  intensityForecast: IntensityForecast
  trackForecast: TrackForecast
  analogues: AnalogueBlock
  risk: RiskBlock
  report: ReportBlock
  verification: VerificationBlock | null
  degraded: boolean
  servedFrom: 'live' | 'cache' | 'demo'
}

// --- model card --------------------------------------------------------------------

export interface DatasetInfo {
  name: string
  source: string
  licence: string
  stormCount: number
  frameCount: number
  matchRatePct: number | null
  note: string | null
}

export interface SplitInfo {
  strategy: 'storm-wise'
  train: number
  val: number
  test: number
  demoStormsInTest: boolean
}

export interface ModelRow {
  key: string
  version: string
  provenance: Provenance
  isTrained: boolean
  metric: string | null
  value: number | null
  baseline: string | null
  baselineValue: number | null
  n: number | null
  notes: string | null
}

export interface AblationRow {
  setting: 'track-only' | 'image-only' | 'fused'
  maeKt: number | null
  n: number | null
}

export interface ConeCalibrationRow {
  leadHours: number
  p67Km: number | null
  p90Km: number | null
  observedContainmentP67: number | null
  n: number | null
}

export interface NotBuiltRow {
  item: string
  reason: string
}

export interface ModelCard {
  bundleVersion: string
  generatedAt: string
  datasets: DatasetInfo[]
  split: SplitInfo
  models: ModelRow[]
  ablation: AblationRow[]
  coneCalibration: ConeCalibrationRow[]
  notBuilt: NotBuiltRow[]
}
