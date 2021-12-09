import Container from '@mui/material/Container';
import AppRoutes from 'routes';
import Navbar from 'components/Navbar';

function App() {
  return (
    <div className="App">
      <Navbar title="Decide Stats Visualizer" />

      <Container maxWidth="xl">
        <AppRoutes />
      </Container>
    </div>
  );
}

export default App;
