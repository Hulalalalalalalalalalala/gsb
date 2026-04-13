import "./App.css";
import { SceneCanvas } from "./components/SceneCanvas";

function App() {
  return (
    <div className="app">
      {/* Top Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-brand">3D Scroll Demo</div>
        <div className="navbar-links">
          <span className="nav-item">Home</span>
          <span className="nav-item">Features</span>
          <span className="nav-item">About</span>
        </div>
      </nav>

      {/* Three.js Canvas - Fixed Background */}
      <div className="scene-wrap">
        <SceneCanvas />
      </div>

      {/* Scrollable Content */}
      <div className="content-container">
        {/* Hero Section - First Screen */}
        <section className="hero-section screen-height">
          <div className="hero-content">
            <h1 className="hero-title">3D Interactive<br />Scroll Experience</h1>
            <p className="hero-subtitle">
              探索三维可视化与网页交互的完美结合<br />
              向下滚动，感受沉浸式体验
            </p>
            <div className="scroll-indicator">
              <span>Scroll Down</span>
              <div className="scroll-arrow">↓</div>
            </div>
          </div>
        </section>

        {/* Feature Section 1 - Left Aligned Card */}
        <section className="feature-section screen-height">
          <div className="glass-card glass-card-left">
            <h2 className="card-title">沉浸式 3D 场景</h2>
            <p className="card-description">
              使用 three.js 创建的高性能三维场景，
              随滚动进度动态变化的视觉效果。
            </p>
            <div className="feature-grid">
              <div className="feature-item">
                <span className="feature-icon">🔮</span>
                <span className="feature-label">实时渲染</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✨</span>
                <span className="feature-label">物理材质</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🎨</span>
                <span className="feature-label">动态光影</span>
              </div>
            </div>
            <div className="card-tags">
              <span className="tag">WebGL</span>
              <span className="tag">Three.js</span>
              <span className="tag">React</span>
            </div>
          </div>
        </section>

        {/* Feature Section 2 - Right Aligned Card */}
        <section className="feature-section screen-height">
          <div className="glass-card glass-card-right">
            <h2 className="card-title">流畅滚动动画</h2>
            <p className="card-description">
              基于滚动进度的平滑动画系统，
              让每个像素的移动都带来视觉变化。
            </p>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">60</div>
                <div className="stat-label">FPS 帧率</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">4</div>
                <div className="stat-label">光源系统</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">1000+</div>
                <div className="stat-label">粒子数量</div>
              </div>
            </div>
            <div className="card-tags">
              <span className="tag">TypeScript</span>
              <span className="tag">Vite</span>
              <span className="tag">响应式</span>
            </div>
          </div>
        </section>

        {/* Footer Section - Last Screen */}
        <section className="footer-section screen-height">
          <div className="footer-content">
            <h2 className="footer-title">项目信息</h2>
            <div className="info-grid">
              <div className="info-item">
                <h3>项目路径</h3>
                <code>/home/hulalalala/gsb/gsb_sample/q0004/cotv21/three-demo</code>
              </div>
              <div className="info-item">
                <h3>本地运行</h3>
                <div className="commands">
                  <code>npm install</code>
                  <code>npm run dev</code>
                  <code>npm run build</code>
                </div>
              </div>
              <div className="info-item">
                <h3>技术栈</h3>
                <div className="tech-stack">
                  <span>Vite + React + TypeScript</span>
                  <span>Three.js + WebGL</span>
                </div>
              </div>
            </div>
            <div className="footer-note">
              © 2024 3D Scroll Demo. Built with modern web technologies.
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
