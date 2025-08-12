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

  if (container === 'centered') {
    return (
      <>
        <div className="h-full w-full flex flex-col items-center justify-center">
          {generatedComponent}
        </div>
        <AccuracyReport />
      </>
    );
  } else {
    return (
      <>
        {generatedComponent}
        <AccuracyReport />
      </>
    );
  }
}

export default App;
