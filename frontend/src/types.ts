// Mirrors app/schemas/common.py (Issue, ReviewResult).
export type Severity = 'error' | 'warning' | 'info'
export type FormType = 'MP-F-023' | 'QS-F-049' | 'MP-F-021' | 'MP-F-018' | 'UNKNOWN'

export interface Issue {
  rule_id: string
  severity: Severity
  page: number
  section: string
  row: string | null
  field: string | null
  message: string
  evidence: string | null
  box_2d: number[] | null
}

export interface FormResult {
  label: string
  page: number
  passed: boolean
  message: string
  issues: Issue[]
  needs_confirmation: Issue[]
}

export interface ReviewResult {
  form_type: FormType
  form_title: string | null
  form_version: string | null
  classification_confidence: number
  passed: boolean
  issues: Issue[]
  needs_confirmation: Issue[]
  pages: number
  processing_ms: number
  message: string | null
  forms: FormResult[]
  page_images: string[]
  page_rotations: number[]
}
