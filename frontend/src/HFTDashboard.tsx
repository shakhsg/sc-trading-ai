import React, { useState, useEffect } from 'react';
import axios from 'axios';
const API = 'http://127.0.0.1:8000';
export default function App() {
  const [state, setState] = useState<any>({ running: false, signals: [], portfolio: [], trades: [], balance: 0, pnl: 0, calls: 0, auto_trade: false, last_scan: 'Never', log: [] });
  useEffect(() => { loadState(); }, []);
  const loadState = async () => { try { const r = await axios.get(API + '/api/state'); setState(r.data); } catch (e) { } };
  const scan = () => axios.post(API + '/api/scan').then(loadState);
  const stop = () => axios.post(API + '/api/stop');
  const doTrade = (t: string, a: string) => axios.post(API + '/api/trade/' + t + '/' + a);
  return (
    <div style={{ fontFamily: '-apple-system,sans-serif', background: '#060610', color: '#c0c8d4', height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ background: '#0a0a18', borderBottom: '1px solid #1a1a30', display: 'flex', alignItems: 'center', height: '44px', padding: '0 16px', gap: '16px' }}>
        <span style={{ color: '#00ff88', fontWeight: 800, fontSize: '16px' }}>SC TRADING AI</span>
        <span style={{ fontSize: '12px', color: '#00bfff' }}>Balance: ${state.balance}</span>
        <span style={{ fontSize: '12px', color: state.pnl >= 0 ? '#00ff88' : '#ff4455' }}>P&L: {state.pnl >= 0 ? '+' : ''}{state.pnl}</span>
        <span style={{ fontSize: '12px', color: '#889' }}>Calls: {state.calls}</span>
        <div style={{ flex: 1 }} />
        <button onClick={scan} style={{ background: '#00ff88', color: '#000', border: 'none', borderRadius: '6px', padding: '6px 14px', fontWeight: 800, cursor: 'pointer' }}>SCAN NOW</button>
        <button onClick={stop} style={{ background: '#ff4455', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 14px', fontWeight: 800, cursor: 'pointer' }}>STOP</button>
        <span style={{ fontSize: '11px', color: state.running ? '#00ff88' : '#334' }}>{state.running ? '● SCANNING' : '● READY'}</span>
      </div>
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '220px 1fr 200px', gap: '1px', background: '#1a1a30', overflow: 'hidden' }}>
        <div style={{ background: '#060610', overflowY: 'auto', padding: '8px' }}>
          <div style={{ fontSize: '10px', color: '#334', textTransform: 'uppercase', marginBottom: '8px' }}>Holdings ({state.portfolio.length})</div>
          {state.portfolio.length === 0 && <div style={{ color: '#223', fontSize: '11px', textAlign: 'center', padding: '16px' }}>No positions yet</div>}
          {state.portfolio.map((p: any) => (
            <div key={p.ticker} style={{ background: '#0a0a18', border: '1px solid #1a1a30', borderRadius: '8px', padding: '8px', marginBottom: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 800, color: '#fff', fontSize: '13px' }}>{p.ticker}</span>
                <span style={{ color: p.pnl >= 0 ? '#00ff88' : '#ff4455', fontWeight: 700 }}>{p.pnl >= 0 ? '+' : ''}{p.pnl}</span>
              </div>
              <div style={{ fontSize: '10px', color: '#334', margin: '3px 0' }}>avg ${p.avg} | now ${p.current} | {p.qty} shares</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '6px' }}>
                <button onClick={() => doTrade(p.ticker, 'BUY')} style={{ background: '#00ff8818', color: '#00ff88', border: '1px solid #00ff8830', borderRadius: '5px', padding: '4px', fontSize: '10px', fontWeight: 800, cursor: 'pointer' }}>BUY MORE</button>
                <button onClick={() => doTrade(p.ticker, 'SELL')} style={{ background: '#ff445518', color: '#ff4455', border: '1px solid #ff445530', borderRadius: '5px', padding: '4px', fontSize: '10px', fontWeight: 800, cursor: 'pointer' }}>SELL</button>
              </div>
            </div>
          ))}
          <div style={{ fontSize: '10px', color: '#334', textTransform: 'uppercase', margin: '12px 0 8px', borderTop: '1px solid #1a1a30', paddingTop: '8px' }}>AI Signals ({state.signals.length})</div>
          {state.signals.length === 0 && <div style={{ color: '#223', fontSize: '11px', textAlign: 'center', padding: '8px' }}>Click Scan Now</div>}
          {state.signals.map((s: any) => (
            <div key={s.ticker} style={{ background: '#0a0a18', border: '1px solid #1a1a30', borderRadius: '8px', padding: '8px', marginBottom: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 800, color: '#fff' }}>{s.ticker} <span style={{ fontSize: '11px', color: '#889' }}>${s.price}</span></span>
                <span style={{ fontSize: '10px', fontWeight: 800, padding: '2px 8px', borderRadius: '8px', background: s.signal === 'BUY' ? '#00ff8818' : s.signal === 'SELL' ? '#ff445518' : '#ffcc0018', color: s.signal === 'BUY' ? '#00ff88' : s.signal === 'SELL' ? '#ff4455' : '#ffcc00' }}>{s.signal} {s.confidence}%</span>
              </div>
              <div style={{ fontSize: '9px', color: '#445', marginBottom: '6px', lineHeight: 1.5 }}>{s.analysis?.substring(0, 80)}...</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                <button onClick={() => doTrade(s.ticker, 'BUY')} style={{ background: '#00ff8818', color: '#00ff88', border: '1px solid #00ff8830', borderRadius: '5px', padding: '4px', fontSize: '10px', fontWeight: 800, cursor: 'pointer' }}>BUY</button>
                <button onClick={() => doTrade(s.ticker, 'SELL')} style={{ background: '#ff445518', color: '#ff4455', border: '1px solid #ff445530', borderRadius: '5px', padding: '4px', fontSize: '10px', fontWeight: 800, cursor: 'pointer' }}>SELL</button>
              </div>
            </div>
          ))}
        </div>
        <div style={{ background: '#060610', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '12px' }}>
          {state.signals.length === 0 ? (
            <>
              <div style={{ fontSize: '48px', color: '#00ff8815', fontWeight: 800 }}>SC</div>
              <div style={{ color: '#223', fontSize: '13px' }}>Click SCAN NOW to load charts and signals</div>
              <div style={{ color: '#112', fontSize: '11px' }}>Last scan: {state.last_scan}</div>
            </>
          ) : (
            <div style={{ width: '100%', height: '100%', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
              {state.signals.map((s: any) => (
                <div key={s.ticker} style={{ background: '#0a0a18', border: '1px solid #1a1a30', borderRadius: '8px', padding: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '16px', fontWeight: 800, color: '#fff' }}>{s.ticker}</span>
                      <span style={{ fontSize: '14px', color: s.signal === 'BUY' ? '#00ff88' : s.signal === 'SELL' ? '#ff4455' : '#ffcc00', fontWeight: 700 }}>${s.price}</span>
                      <span style={{ fontSize: '10px', fontWeight: 800, padding: '3px 10px', borderRadius: '10px', background: s.signal === 'BUY' ? '#00ff8818' : '#ff445518', color: s.signal === 'BUY' ? '#00ff88' : '#ff4455' }}>{s.signal} · {s.confidence}%</span>
                      {s.congress && <span style={{ fontSize: '10px', color: '#00bfff', background: '#00bfff10', border: '1px solid #00bfff20', padding: '2px 8px', borderRadius: '6px' }}>🏛 Congress Signal</span>}
                    </div>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button onClick={() => doTrade(s.ticker, 'BUY')} style={{ background: '#00ff88', color: '#000', border: 'none', borderRadius: '6px', padding: '6px 14px', fontSize: '12px', fontWeight: 800, cursor: 'pointer' }}>BUY {s.ticker}</button>
                      <button onClick={() => doTrade(s.ticker, 'SELL')} style={{ background: '#ff4455', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 14px', fontSize: '12px', fontWeight: 800, cursor: 'pointer' }}>SELL</button>
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', color: '#556', lineHeight: 1.6 }}>{s.analysis}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div style={{ background: '#060610', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
            <div style={{ fontSize: '10px', color: '#334', textTransform: 'uppercase', marginBottom: '8px' }}>Market News</div>
            {[{ t: 'AAPL', ti: 'Apple reports record iPhone sales in Asia', b: true }, { t: 'NVDA', ti: 'Nvidia AI chip demand surges ahead of earnings', b: true }, { t: 'MSFT', ti: 'Microsoft Azure beats revenue estimates', b: true }, { t: 'META', ti: 'Meta ad revenue grows 20% year over year', b: true }, { t: 'MARKETS', ti: 'Fed signals one rate cut expected in 2025', b: false }].map((n, i) => (
              <div key={i} style={{ padding: '6px 4px', borderBottom: '1px solid #0a0a18' }}>
                <div style={{ display: 'flex', gap: '6px', marginBottom: '3px' }}>
                  <span style={{ fontSize: '8px', fontWeight: 800, padding: '1px 5px', borderRadius: '3px', background: n.b ? '#00ff8818' : '#ff445518', color: n.b ? '#00ff88' : '#ff4455' }}>{n.t}</span>
                </div>
                <div style={{ fontSize: '10px', color: '#778', lineHeight: 1.4 }}>{n.ti}</div>
              </div>
            ))}
          </div>
          <div style={{ borderTop: '1px solid #1a1a30', padding: '8px', maxHeight: '200px', overflowY: 'auto' }}>
            <div style={{ fontSize: '10px', color: '#334', textTransform: 'uppercase', marginBottom: '6px' }}>Bot Log</div>
            {state.log.slice(0, 10).map((l: string, i: number) => (
              <div key={i} style={{ fontSize: '9px', color: '#2a3050', lineHeight: 1.8, fontFamily: 'monospace' }}>{l}</div>
            ))}
            {state.log.length === 0 && <div style={{ color: '#1a1a30', fontSize: '10px' }}>No logs yet</div>}
          </div>
        </div>
      </div>
      <div style={{ height: '80px', background: '#0a0a18', borderTop: '1px solid #1a1a30', padding: '8px 16px', overflowX: 'auto', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <div style={{ fontSize: '10px', color: '#334', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>Trade History</div>
        {state.trades.length === 0 && <div style={{ color: '#1a1a30', fontSize: '11px' }}>No trades yet</div>}
        {state.trades.slice(0, 8).map((t: any, i: number) => (
          <div key={i} style={{ background: '#060610', border: '1px solid #1a1a30', borderRadius: '6px', padding: '6px 10px', whiteSpace: 'nowrap', fontSize: '11px' }}>
            <span style={{ color: t.action === 'BUY' ? '#00ff88' : '#ff4455', fontWeight: 800 }}>{t.action}</span>
            <span style={{ color: '#fff', marginLeft: '4px' }}>{t.ticker}</span>
            <span style={{ color: '#556', marginLeft: '4px' }}>${t.price}</span>
            <span style={{ color: '#334', marginLeft: '4px' }}>{t.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
