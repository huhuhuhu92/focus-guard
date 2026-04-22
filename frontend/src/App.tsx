import { useState } from 'react';
import { Settings } from './components/Settings';
import { Statistics } from './components/Statistics';

export default function App() {
  const [activeTab, setActiveTab] = useState<'settings' | 'statistics'>('settings');

  return (
    <div className="min-h-screen bg-[#ECECEC] flex justify-center text-[#3A3A3A]" style={{ fontFamily: '"Inter", system-ui, sans-serif' }}>
      <div className="w-full px-4 sm:px-6 py-6 sm:py-7 max-w-[720px]">
        <header className="flex flex-col sm:flex-row sm:items-center justify-between mb-7 gap-3 sm:gap-0">
          <div>
            <div className="text-[11px] tracking-[0.2em] text-[#A8A8A8] uppercase">Focus</div>
            <h1 className="text-[#3A3A3A] text-[17px] tracking-wide mt-0.5" style={{ fontWeight: 400 }}>Reminder</h1>
          </div>

          <nav className="flex gap-1 p-1 rounded-full bg-[#ECECEC] shadow-[inset_3px_3px_6px_#c9cfd6,inset_-3px_-3px_6px_#ffffff] self-start sm:self-auto">
            {(['settings', 'statistics'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-1.5 rounded-full transition-all duration-300 text-[12px] tracking-wider ${
                  activeTab === tab
                    ? 'bg-[#ECECEC] shadow-[3px_3px_6px_#c9cfd6,-3px_-3px_6px_#ffffff] text-[#3A3A3A]'
                    : 'text-[#A8A8A8] hover:text-[#6A6A6A]'
                }`}
                style={{ fontWeight: 400 }}
              >
                {tab === 'settings' ? '设置' : '统计'}
              </button>
            ))}
          </nav>
        </header>

        {activeTab === 'settings' ? <Settings onOpenStatistics={() => setActiveTab('statistics')} /> : <Statistics />}
      </div>
    </div>
  );
}
