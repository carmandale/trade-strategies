import { useMemo, useState } from 'react';
import { Container, Theme } from './settings/types';
import SPYSpreadStrategiesApp from './components/generated/SPYSpreadStrategiesApp';
import ConsolidatedSPYApp from './components/ConsolidatedSPYApp';
import { AccuracyReport } from './components/AccuracyReport';

const theme: Theme = 'dark';
const container: Container = 'none';

function App() {
  const [useConsolidatedLayout, setUseConsolidatedLayout] = useState(true); // Default to new layout

  function setTheme(theme: Theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  setTheme(theme);

  const generatedComponent = useMemo(() => {
    // Switch between layouts for comparison
    if (useConsolidatedLayout) {
      return <ConsolidatedSPYApp />;
    } else {
      return <SPYSpreadStrategiesApp />; // Original layout
    }
  }, [useConsolidatedLayout]);

  const toggleButton = (
    <div className="fixed top-4 right-4 z-50">
      <button
        onClick={() => setUseConsolidatedLayout(!useConsolidatedLayout)}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
      >
        {useConsolidatedLayout ? 'Switch to Original' : 'Switch to Consolidated'}
      </button>
    </div>
  );

  if (container === 'centered') {
    return (
      <>
        {toggleButton}
        <div className="h-full w-full flex flex-col items-center justify-center">
          {generatedComponent}
        </div>
        <AccuracyReport />
      </>
    );
  } else {
    return (
      <>
        {toggleButton}
        {generatedComponent}
        <AccuracyReport />
      </>
    );
  }
}

export default App;
