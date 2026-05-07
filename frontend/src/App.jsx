import { useState } from 'react'

function App() {
  const [a, setA] = useState('')
  const [b, setB] = useState('')
  const [op, setOp] = useState('+')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleCalc = async () => {
    setError('')
    setResult(null)

    try {
      const res = await fetch('http://localhost:8000/calc', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          a: Number(a),
          b: Number(b),
          op: op,
        }),
      })

      const data = await res.json()

      if (data.error) {
        setError(data.error)
      } else {
        setResult(data.result)
      }
    } catch (err) {
      setError('请求失败')
      console.error(err)
    }
  }

  return (
    <div style={{ textAlign: 'center', marginTop: '100px' }}>
      <h2>Calculator</h2>

      <div>
        <input
          type="number"
          placeholder="a"
          value={a}
          onChange={(e) => setA(e.target.value)}
        />
      </div>

      <div>
        <select value={op} onChange={(e) => setOp(e.target.value)}>
          <option value="+">+</option>
          <option value="-">-</option>
          <option value="*">*</option>
          <option value="/">/</option>
        </select>
      </div>

      <div>
        <input
          type="number"
          placeholder="b"
          value={b}
          onChange={(e) => setB(e.target.value)}
        />
      </div>

      <div style={{ marginTop: '10px' }}>
        <button onClick={handleCalc}>计算</button>
      </div>

      <div style={{ marginTop: '20px' }}>
        {result !== null && <h3>结果: {result}</h3>}
        {error && <h3 style={{ color: 'red' }}>{error}</h3>}
      </div>
    </div>
  )
}

export default App