import Script from 'next/script';

export default function WidgetTestPage() {
  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          min-height: 100vh;
        }
        .demo-header {
          background: white;
          padding: 20px 40px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .demo-header h1 {
          color: #333;
          font-size: 24px;
        }
        .demo-header p {
          color: #666;
          margin-top: 5px;
        }
        .demo-content {
          max-width: 800px;
          margin: 60px auto;
          padding: 40px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .demo-content h2 {
          color: #333;
          margin-bottom: 20px;
        }
        .demo-content p {
          color: #555;
          line-height: 1.8;
          margin-bottom: 15px;
        }
        .code-block {
          background: #1e1e2e;
          color: #cdd6f4;
          padding: 20px;
          border-radius: 8px;
          font-family: 'Monaco', 'Consolas', monospace;
          font-size: 14px;
          margin: 20px 0;
          overflow-x: auto;
        }
        .instructions {
          background: #e3f2fd;
          padding: 20px;
          border-radius: 8px;
          margin: 20px 0;
          border-left: 4px solid #03a9f4;
        }
        .instructions h3 {
          color: #0277bd;
          margin-bottom: 10px;
        }
        .instructions ol {
          color: #555;
          padding-left: 20px;
        }
        .instructions li {
          margin-bottom: 8px;
        }
        .test-note {
          background: #fff3e0;
          padding: 15px 20px;
          border-radius: 8px;
          color: #e65100;
          margin-top: 20px;
        }
        .feature-list {
          margin-left: 20px;
          color: #555;
          line-height: 2;
        }
      `}</style>
      
      <div className="demo-header">
        <h1>JoveHeal Website (Demo)</h1>
        <p>This simulates how the Jovee widget will appear on your Kajabi site</p>
      </div>

      <div className="demo-content">
        <h2>Jovee Chat Widget Test Page</h2>
        
        <p>
          This page demonstrates the embeddable Jovee chat widget. Look at the 
          <strong> bottom-right corner</strong> of this page - you&apos;ll see a floating 
          chat bubble. Click it to open the chat!
        </p>

        <div className="instructions">
          <h3>How to Add to Kajabi:</h3>
          <ol>
            <li>Log into your Kajabi dashboard</li>
            <li>Go to <strong>Website</strong> → <strong>Pages</strong></li>
            <li>Open your page in the editor</li>
            <li>Add a <strong>Custom Code</strong> section</li>
            <li>Paste the code below</li>
            <li>Save and publish</li>
          </ol>
        </div>

        <div className="code-block">
          <span style={{color: '#6c7086'}}>&lt;!-- Jovee Chat Widget - Add this to your Kajabi page --&gt;</span><br/>
          <span style={{color: '#f38ba8'}}>&lt;script</span> <span style={{color: '#a6e3a1'}}>src</span>=<span style={{color: '#f9e2af'}}>&quot;https://jove.sam9scloud.in/widget.js&quot;</span><span style={{color: '#f38ba8'}}>&gt;&lt;/script&gt;</span>
        </div>

        <p>
          That&apos;s it! Just one line of code adds the full Jovee chat experience to 
          any page on your website. The widget will:
        </p>

        <ul className="feature-list">
          <li>Display a floating chat bubble in the bottom-right corner</li>
          <li>Open a chat window when clicked</li>
          <li>Connect to Jovee for AI-powered responses</li>
          <li>Stream responses in real-time</li>
          <li>Support clickable links to JoveHeal programs</li>
          <li>Work on mobile and desktop</li>
          <li>Drag top-left corner to resize the widget</li>
        </ul>

        <div className="test-note">
          <strong>Testing:</strong> Click the blue chat bubble in the bottom-right corner 
          to test the widget. Try asking about JoveHeal programs! You can also drag the top-left corner to resize the chat window.
        </div>
      </div>

      <Script src="/widget.js" strategy="afterInteractive" />
    </>
  );
}
