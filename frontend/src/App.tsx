import { HealthStatus } from "./components/HealthStatus";

export default function App() {
  return (
    <main className="app-shell">
      <header>
        <h1>MealRoulette</h1>
        <p>Household meal planning, starting with the API foundation.</p>
      </header>
      <HealthStatus />
    </main>
  );
}
