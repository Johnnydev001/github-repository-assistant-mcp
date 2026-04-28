import React, {useState} from 'react'

export default function ReadFileForm() {
  const [path, setPath] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      // Adapter endpoint: /api/read-file - implement server-side bridge that runs MCP client or server call
      const resp = await fetch('/api/read-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      if (!resp.ok) {
        const txt = await resp.text()
        throw new Error(txt || 'Request failed')
      }
      const text = await resp.text()
      setResult(text)
    } catch (err: any) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3>Read file</h3>
      <form onSubmit={handleSubmit}>
        <label>
          Repository path
          <input value={path} onChange={e => setPath(e.target.value)} placeholder="e.g. README.md" />
        </label>
        <div className="actions">
          <button type="submit" disabled={loading || !path}>Read</button>
        </div>
      </form>

      {loading && <div className="status">Loading…</div>}
      {error && <div className="error">{error}</div>}
      {result && (
        <pre className="result">{result}</pre>
      )}
    </div>
  )
}
