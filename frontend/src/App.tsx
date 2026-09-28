import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import type { FormResult, Issue, ReviewResult } from './types'

const MAX_MB = 20
const REQUEST_TIMEOUT_MS = 5 * 60 * 1000

type State =
  | { kind: 'idle' }
  | { kind: 'loading'; file: File; startedAt: number }
  | { kind: 'done'; file: File; result: ReviewResult }
  | { kind: 'error'; file: File | null; message: string }

export default function App() {
  const [state, setState] = useState<State>({ kind: 'idle' })

  async function review(file: File) {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      setState({ kind: 'error', file, message: 'Please choose a PDF file.' })
      return
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setState({ kind: 'error', file, message: `The file is larger than ${MAX_MB} MB.` })
      return
    }
    setState({ kind: 'loading', file, startedAt: Date.now() })
    const body = new FormData()
    body.append('file', file)
    try {
      const resp = await fetch('/api/review', {
        method: 'POST',
        body,
        signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
      })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) {
        const detail = typeof data.detail === 'string' ? data.detail : 'Something went wrong.'
        setState({ kind: 'error', file, message: detail })
        return
      }
      setState({ kind: 'done', file, result: data as ReviewResult })
    } catch (err) {
      const timedOut = err instanceof DOMException && err.name === 'TimeoutError'
      setState({
        kind: 'error',
        file,
        message: timedOut
          ? 'The review took too long. Please try again.'
          : 'Could not reach the reviewer. Check your connection and try again.',
      })
    }
  }

  const reset = () => setState({ kind: 'idle' })

  return (
    <div className="flex min-h-screen flex-col">
      <div className="bg-green px-4 py-1.5 text-center text-xs font-semibold uppercase tracking-wider text-white">
        Internal tool · RegenMed staff use only
      </div>
      <header className="border-b-4 border-brand bg-white">
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
          <img src="/beacon.svg" alt="" className="h-10 w-10" />
          <h1 className="text-xl font-bold leading-tight">Beacon Document Reviewer</h1>
        </div>
      </header>

      <main className={`mx-auto flex w-full flex-1 flex-col px-4 py-8 ${state.kind === 'done' ? 'max-w-6xl' : 'max-w-4xl'}`}>
        {state.kind === 'idle' && (
          <div className="my-auto">
            <UploadZone onFile={review} />
            <Tagline className="mt-5" />
          </div>
        )}
        {state.kind === 'loading' && (
          <div className="my-auto">
            <Progress file={state.file} startedAt={state.startedAt} />
          </div>
        )}
        {state.kind === 'error' && (
          <ErrorPanel message={state.message} file={state.file} onRetry={review} onReset={reset} />
        )}
        {state.kind === 'done' && <Report file={state.file} result={state.result} onReset={reset} />}
      </main>

      {state.kind !== 'idle' && (
        <footer className="mx-auto max-w-4xl px-4 pb-10 pt-4">
          <Tagline />
        </footer>
      )}
    </div>
  )
}

function Tagline({ className = '' }: { className?: string }) {
  return (
    <p className={`text-center text-xs text-slate-500 ${className}`}>
      RegenMed's document reviewer that pre-screens processing forms to prevent errors and keep
      records accurate.
    </p>
  )
}

function UploadZone({ onFile }: { onFile: (f: File) => void }) {
  const [dragging, setDragging] = useState(false)
  const input = useRef<HTMLInputElement>(null)

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => input.current?.click()}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        const files = e.dataTransfer.files
        if (files.length > 1) alert('Please upload one PDF at a time.')
        if (files[0]) onFile(files[0])
      }}
      className={`cursor-pointer rounded-2xl border-2 border-dashed bg-white px-6 py-16 text-center transition ${
        dragging ? 'border-brand bg-brand-soft' : 'border-slate-300 hover:border-brand'
      }`}
    >
      <div className="text-5xl">📄</div>
      <p className="mt-4 text-lg font-medium">Drop a scanned form here</p>
      <p className="mt-1 text-sm text-slate-500">or click to choose a PDF (one file, up to {MAX_MB} MB)</p>
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
    </div>
  )
}

function Progress({ file, startedAt }: { file: File; startedAt: number }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 500)
    return () => clearInterval(t)
  }, [])
  const secs = Math.floor((now - startedAt) / 1000)
  const step =
    secs < 6 ? 'Identifying the form…' : secs < 40 ? 'Reading every field on the form…' : 'Almost there — checking every row…'

  return (
    <div className="rounded-2xl bg-white px-6 py-14 text-center shadow-sm">
      <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-soft border-t-brand" />
      <p className="mt-5 text-lg font-medium">{step}</p>
      <p className="mt-1 text-sm text-slate-500">
        {file.name}
      </p>
    </div>
  )
}

function ErrorPanel(props: {
  message: string
  file: File | null
  onRetry: (f: File) => void
  onReset: () => void
}) {
  return (
    <div className="rounded-2xl border border-fail/30 bg-fail-soft px-6 py-8">
      <p className="font-semibold text-fail">We couldn't review this file</p>
      <p className="mt-1 text-slate-700">{props.message}</p>
      <div className="mt-5 flex gap-3">
        {props.file && (
          <button onClick={() => props.onRetry(props.file!)} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark">
            Try again
          </button>
        )}
        <button onClick={props.onReset} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium">
          Choose another file
        </button>
      </div>
    </div>
  )
}

type Box = number[]
interface Highlight {
  numbers: Map<string, number>
  boxes: Map<string, Box>
  selected: string | null
  select: (key: string) => void
}
const HighlightContext = createContext<Highlight | null>(null)
const issueKey = (i: Issue) => [i.rule_id, i.page, i.row, i.field, i.message].join('|')

function useLocate(file: File, result: ReviewResult) {
  const all = useMemo(() => {
    const errs = result.issues.filter((i) => i.severity === 'error')
    const info = result.issues.filter((i) => i.severity === 'info')
    return [...errs, ...result.needs_confirmation, ...info]
  }, [result])
  const [boxes, setBoxes] = useState<Map<string, Box>>(new Map())
  const [status, setStatus] = useState<'idle' | 'locating' | 'done' | 'failed'>('idle')

  useEffect(() => {
    if (!all.length || !result.page_images?.length) return
    const body = new FormData()
    body.append('file', file)
    body.append('issues', JSON.stringify(all))
    body.append('rotations', JSON.stringify(result.page_rotations ?? []))
    setStatus('locating')
    fetch('/api/locate', { method: 'POST', body, signal: AbortSignal.timeout(120000) })
      .then((r) => (r.ok ? r.json() : Promise.reject(r)))
      .then((data: { boxes: (Box | null)[] }) => {
        const found = new Map<string, Box>()
        data.boxes.forEach((b, n) => b && found.set(issueKey(all[n]), b))
        setBoxes(found)
        setStatus('done')
      })
      .catch(() => setStatus('failed'))
  }, [all, file, result])

  const numbers = useMemo(() => {
    const m = new Map<string, number>()
    all.filter((i) => boxes.has(issueKey(i))).forEach((i, n) => m.set(issueKey(i), n + 1))
    return m
  }, [all, boxes])
  return { all, boxes, numbers, status }
}

function Report({ file, result, onReset }: { file: File; result: ReviewResult; onReset: () => void }) {
  const errors = result.issues.filter((i) => i.severity === 'error')
  const notes = result.issues.filter((i) => i.severity === 'info')
  const unknown = result.form_type === 'UNKNOWN'
  const { all, boxes, numbers, status } = useLocate(file, result)
  const [selected, setSelected] = useState<string | null>(null)
  const highlight: Highlight = { numbers, boxes, selected, select: setSelected }
  const showPreview = !unknown && all.length > 0 && result.page_images?.length > 0


  return (
    <HighlightContext.Provider value={highlight}>
    <div className={showPreview ? 'grid gap-6 lg:grid-cols-[minmax(0,1fr)_420px]' : ''}>
    <div className="min-w-0 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Detected form</div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-brand px-2.5 py-1 font-mono text-lg font-semibold text-white">
              {result.form_type}
              {result.form_version && <span className="opacity-70">.{result.form_version}</span>}
            </span>
            {result.form_title && <span className="text-lg font-medium">{result.form_title}</span>}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            {file.name} · {result.pages} page{result.pages === 1 ? '' : 's'}
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={onReset} className="rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand-dark">
            Check another form
          </button>
        </div>
      </div>

      <Banner result={result} />

      {result.forms.length > 1 ? (
        result.forms.map((form) => <FormCard key={form.page} form={form} />)
      ) : (
        <Findings errors={errors} notes={notes} needsConfirmation={result.needs_confirmation} />
      )}

      {!unknown && result.passed && errors.length === 0 && (
        <p className="text-center text-sm text-slate-500">Every check for {result.form_type} passed.</p>
      )}
    </div>
    {showPreview && (
      <PagePreview images={result.page_images} all={all} status={status} />
    )}
    </div>
    </HighlightContext.Provider>
  )
}

function PagePreview(props: { images: string[]; all: Issue[]; status: string }) {
  const hl = useContext(HighlightContext)!
  const pages = [...new Set(props.all.map((i) => i.page))].filter((p) => p <= props.images.length).sort((a, b) => a - b)
  const located = props.all.filter((i) => hl.boxes.has(issueKey(i))).length
  return (
    <aside className="lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto">
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
        Where on the form
        {props.status === 'locating' && (
          <span className="flex items-center gap-1.5 text-xs font-normal text-slate-500">
            <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand-soft border-t-brand" />
            Locating issues…
          </span>
        )}
        {props.status === 'done' && (
          <span className="text-xs font-normal text-slate-500">
            {located} of {props.all.length} located · click an issue to find it
          </span>
        )}
        {props.status === 'failed' && <span className="text-xs font-normal text-slate-500">Highlighting unavailable</span>}
      </div>
      <div className="space-y-4">
        {pages.map((p) => (
          <div key={p} className="relative overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <div className="absolute left-2 top-2 z-10 rounded bg-slate-800/75 px-1.5 py-0.5 text-[10px] font-semibold text-white">Page {p}</div>
            <img src={props.images[p - 1]} alt={`Page ${p}`} className="block w-full" />
            {props.all.filter((i) => i.page === p && hl.boxes.has(issueKey(i))).map((i) => {
              const key = issueKey(i)
              const [y0, x0, y1, x1] = hl.boxes.get(key)!
              const active = hl.selected === key
              const tone = i.severity === 'error' ? 'border-brand' : i.severity === 'warning' ? 'border-warn' : 'border-green'
              return (
                <button
                  key={key}
                  id={`box-${key}`}
                  onClick={() => hl.select(key)}
                  title={i.message}
                  className={`absolute rounded-sm border-2 ${tone} transition ${active ? 'bg-brand/30 ring-4 ring-brand/40' : 'bg-brand/10 hover:bg-brand/20'}`}
                  style={{ top: `${y0 / 10}%`, left: `${x0 / 10}%`, width: `${(x1 - x0) / 10}%`, height: `${(y1 - y0) / 10}%` }}
                >
                  <span className="absolute -left-2 -top-2 grid h-4 min-w-4 place-items-center rounded-full bg-brand px-1 text-[9px] font-bold text-white">
                    {hl.numbers.get(key)}
                  </span>
                </button>
              )
            })}
          </div>
        ))}
      </div>
    </aside>
  )
}

function Findings(props: { errors: Issue[]; notes: Issue[]; needsConfirmation: Issue[] }) {
  const { errors, notes, needsConfirmation } = props
  return (
    <>
      {errors.length > 0 && (
        <Section title={`Issues to fix (${errors.length})`}>
          {groupBySection(errors).map(([section, items]) => (
            <IssueGroup key={section} title={section} issues={items} />
          ))}
        </Section>
      )}
      {needsConfirmation.length > 0 && (
        <Section
          title={`Needs confirmation (${needsConfirmation.length})`}
          hint="Please check these on the paper form: entries that couldn't be read with confidence, or that look unusual. They don't fail the form on their own."
        >
          <IssueGroup issues={needsConfirmation} />
        </Section>
      )}
      {notes.length > 0 && (
        <Section title={`Notes (${notes.length})`}>
          <IssueGroup issues={notes} />
        </Section>
      )}
    </>
  )
}

function FormCard({ form }: { form: FormResult }) {
  const errors = form.issues.filter((i) => i.severity === 'error')
  const notes = form.issues.filter((i) => i.severity === 'info')
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className={`flex flex-wrap items-center justify-between gap-2 px-5 py-3 ${form.passed ? 'bg-pass-soft' : 'bg-fail-soft'}`}>
        <div className="font-semibold">{form.label}</div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-slate-500">Page {form.page}</span>
          <span className={`rounded-md px-2 py-0.5 text-sm font-bold text-white ${form.passed ? 'bg-pass' : 'bg-fail'}`}>
            {form.passed ? '✓ PASS' : '✕ FAIL'}
          </span>
        </div>
      </div>
      <div className="space-y-4 px-5 py-4">
        <p className="text-sm text-slate-700">{form.message}</p>
        <Findings errors={errors} notes={notes} needsConfirmation={form.needs_confirmation} />
      </div>
    </div>
  )
}

function Banner({ result }: { result: ReviewResult }) {
  if (result.form_type === 'UNKNOWN') {
    return (
      <div className="rounded-2xl border border-warn/30 bg-warn-soft px-6 py-5">
        <div className="text-xl font-bold text-warn">Unsupported form</div>
        <p className="mt-1 text-slate-700">{result.message}</p>
      </div>
    )
  }
  const pass = result.passed
  return (
    <div className={`rounded-2xl border px-6 py-5 ${pass ? 'border-pass/30 bg-pass-soft' : 'border-fail/30 bg-fail-soft'}`}>
      <div className={`text-2xl font-bold ${pass ? 'text-pass' : 'text-fail'}`}>{pass ? '✓ PASS' : '✕ FAIL'}</div>
      <p className="mt-1 text-slate-700">{result.message}</p>
    </div>
  )
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-base font-semibold">{title}</h2>
      {hint && <p className="mt-0.5 text-sm text-slate-500">{hint}</p>}
      <div className="mt-3 space-y-4">{children}</div>
    </section>
  )
}

function IssueGroup({ title, issues }: { title?: string; issues: Issue[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      {title && <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold">{title}</div>}
      <ul className="divide-y divide-slate-100">
        {issues.map((issue, i) => (
          <IssueRow key={i} issue={issue} showSection={!title} />
        ))}
      </ul>
    </div>
  )
}

const CHIP: Record<Issue['severity'], string> = {
  error: 'bg-fail-soft text-fail',
  warning: 'bg-warn-soft text-warn',
  info: 'bg-info-soft text-info',
}
const CHIP_LABEL: Record<Issue['severity'], string> = { error: 'Error', warning: 'Check', info: 'Note' }

function IssueRow({ issue, showSection }: { issue: Issue; showSection: boolean }) {
  const section = showSection ? issue.section.replace(/^Page \d+ – /, '') : null
  const where = [section, issue.row, issue.field].filter(Boolean).join(' · ')
  const hl = useContext(HighlightContext)
  const key = issueKey(issue)
  const number = hl?.numbers.get(key)
  const active = hl?.selected === key
  const select = () => {
    if (!hl || !number) return
    hl.select(key)
    document.getElementById(`box-${key}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  return (
    <li
      onClick={select}
      className={`flex gap-3 px-4 py-3 ${number ? 'cursor-pointer hover:bg-brand-soft/60' : ''} ${active ? 'bg-brand-soft' : ''}`}
    >
      {number !== undefined && (
        <span className="mt-0.5 grid h-5 min-w-5 shrink-0 place-items-center rounded-full bg-brand px-1 text-[10px] font-bold text-white">
          {number}
        </span>
      )}
      <span className={`mt-0.5 h-fit shrink-0 rounded px-2 py-0.5 text-xs font-semibold ${CHIP[issue.severity]}`}>
        {CHIP_LABEL[issue.severity]}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm">{issue.message}</p>
        <p className="mt-0.5 text-xs text-slate-500">
          Page {issue.page}
          {where && ` · ${where}`}
          <span className="ml-2 font-mono text-slate-400">{issue.rule_id}</span>
        </p>
      </div>
    </li>
  )
}

function groupBySection(issues: Issue[]): [string, Issue[]][] {
  const groups = new Map<string, Issue[]>()
  for (const issue of issues) {
    const key = `Page ${issue.page} – ${issue.section.replace(/^Page \d+ – /, '')}`
    groups.set(key, [...(groups.get(key) ?? []), issue])
  }
  return [...groups.entries()]
}
