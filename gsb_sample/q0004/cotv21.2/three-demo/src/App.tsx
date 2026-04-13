import "./App.css";
import { SceneCanvas } from "./components/SceneCanvas";

function App() {
  return (
    <div className="app">
      <SceneCanvas />
      
      <nav className="top-nav">
        <span className="nav-brand">3D Scroll Experience</span>
        <div className="nav-links">
          <a href="#hero" className="nav-link">首页</a>
          <a href="#features" className="nav-link">特性</a>
          <a href="#about" className="nav-link">关于</a>
          <a href="#contact" className="nav-link">联系</a>
        </div>
      </nav>

      <section id="hero" className="section hero-section">
        <div className="hero-content">
          <h1 className="hero-title">沉浸式三维滚动体验</h1>
          <p className="hero-subtitle">
            随着页面滚动，探索三维场景的动态变化。
            主物体旋转、相机移动、灯光变化，每一次滚动都是新的视觉体验。
          </p>
          <div className="scroll-indicator">
            <span>向下滚动探索</span>
            <div className="scroll-arrow"></div>
          </div>
        </div>
      </section>

      <section id="features" className="section features-section">
        <div className="glass-card card-left">
          <div className="card-header">
            <h2 className="card-title">核心特性</h2>
            <span className="chip chip-primary">Three.js</span>
          </div>
          <div className="card-content">
            <div className="feature-list">
              <div className="feature-item">
                <div className="feature-icon">🎨</div>
                <div className="feature-text">
                  <h3>动态渲染</h3>
                  <p>实时三维渲染，流畅动画效果</p>
                </div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">📱</div>
                <div className="feature-text">
                  <h3>响应式设计</h3>
                  <p>完美适配各种屏幕尺寸</p>
                </div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">⚡</div>
                <div className="feature-text">
                  <h3>高性能</h3>
                  <p>优化的渲染管线，60fps 流畅体验</p>
                </div>
              </div>
            </div>
            <div className="tag-cloud">
              <span className="tag">WebGL</span>
              <span className="tag">React</span>
              <span className="tag">TypeScript</span>
              <span className="tag">Vite</span>
              <span className="tag">3D</span>
            </div>
          </div>
        </div>
      </section>

      <section id="about" className="section about-section">
        <div className="glass-card card-right">
          <div className="card-header">
            <h2 className="card-title">项目统计</h2>
            <span className="chip chip-secondary">数据可视化</span>
          </div>
          <div className="card-content">
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">1000+</div>
                <div className="stat-label">粒子数量</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">60</div>
                <div className="stat-label">FPS 目标</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">3</div>
                <div className="stat-label">灯光系统</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">5</div>
                <div className="stat-label">动画元素</div>
              </div>
            </div>
            <div className="capsule-list">
              <div className="capsule">
                <span className="capsule-label">加载时间</span>
                <span className="capsule-value">&lt; 2s</span>
              </div>
              <div className="capsule">
                <span className="capsule-label">兼容性</span>
                <span className="capsule-value">现代浏览器</span>
              </div>
              <div className="capsule">
                <span className="capsule-label">构建大小</span>
                <span className="capsule-value">&lt; 500KB</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="contact" className="section footer-section">
        <div className="footer-content">
          <h2 className="footer-title">开始使用</h2>
          <p className="footer-description">
            这是一个基于 Vite + React + TypeScript + Three.js 的三维滚动演示项目。
            滚动页面即可看到三维场景随阅读进度而变化。
          </p>
          
          <div className="setup-steps">
            <div className="setup-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>安装依赖</h3>
                <code>npm install</code>
              </div>
            </div>
            <div className="setup-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>启动开发服务器</h3>
                <code>npm run dev</code>
              </div>
            </div>
            <div className="setup-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>构建生产版本</h3>
                <code>npm run build</code>
              </div>
            </div>
          </div>
          
          <div className="footer-bottom">
            <p>项目路径: /home/hulalalala/gsb/gsb_sample/q0004/cotv21.2/three-demo</p>
            <p className="copyright">© 2024 3D Scroll Experience Demo</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;
