import { useMemo } from 'react';
import { Container, Theme } from './settings/types';
import SPYSpreadStrategiesApp from './components/generated/SPYSpreadStrategiesApp';
import { AccuracyReport } from './components/AccuracyReport';

const theme: Theme = 'dark';
const container: Container = 'none';

function App() {
  function setTheme(theme: Theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  setTheme(theme);

  const generatedComponent = useMemo(() => {
    // THIS IS WHERE THE TOP LEVEL GENRATED COMPONENT WILL BE RETURNED!
    return <SPYSpreadStrategiesApp />; // %EXPORT_STATEMENT%
  }, []);

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
