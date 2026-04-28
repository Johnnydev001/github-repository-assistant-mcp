import React, {useState} from 'react'
import ReadFileForm from './components/ReadFileForm'

export default function App() {
  const [selected, setSelected] = useState<'read-file' | null>('read-file')

  return (
    <div className="app-root">
      <aside className="sidebar">
        <h3>Actions</h3>
        <button className={selected==='read-file' ? 'active' : ''} onClick={()=>setSelected('read-file')}>Read file</button>
      </aside>
      <main className="main">
        <header className="topbar">
          <h2>Portfolio MCP UI</h2>
        </header>
        <section className="content">
          {selected === 'read-file' && <ReadFileForm />}
        </section>
      </main>
    </div>
  )
}
