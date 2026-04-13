import "./App.css";
import { Globe } from "./components/Globe";

function App() {
  return (
    <div className="app">
      <h1 className="brand">
        <a
          className="brand-cobe"
          href="https://github.com/shuding/cobe"
          target="_blank"
          rel="noreferrer"
        >
          cobe
        </a>
        <span className="brand-webgl"> WebGL</span>
      </h1>
      <div className="globe-wrap">
        <Globe />
      </div>
    </div>
  );
}

export default App;
