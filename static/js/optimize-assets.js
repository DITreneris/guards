const fs = require('fs');
const path = require('path');
const { minify } = require('terser');
const CleanCSS = require('clean-css');

// Directories
const jsDir = path.join(__dirname, '../js');
const cssDir = path.join(__dirname, '../css');
const distDir = path.join(__dirname, '../dist');

// Create dist directory if it doesn't exist
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// Minify JS
async function minifyJS() {
  try {
    // Read script.js
    const jsContent = fs.readFileSync(path.join(jsDir, 'script.js'), 'utf8');
    
    // Minify with terser
    const minified = await minify(jsContent, {
      compress: {
        drop_console: true,
        drop_debugger: true
      },
      mangle: true
    });
    
    // Write to dist folder
    fs.writeFileSync(path.join(distDir, 'script.min.js'), minified.code);
    console.log('JavaScript minified successfully');
  } catch (err) {
    console.error('Error minifying JavaScript:', err);
  }
}

// Minify CSS
function minifyCSS() {
  try {
    // Read styles.css
    const cssContent = fs.readFileSync(path.join(cssDir, 'styles.css'), 'utf8');
    
    // Minify with clean-css
    const minified = new CleanCSS({
      level: 2,
      compatibility: 'ie10'
    }).minify(cssContent);
    
    // Write to dist folder
    fs.writeFileSync(path.join(distDir, 'styles.min.css'), minified.styles);
    console.log('CSS minified successfully');
  } catch (err) {
    console.error('Error minifying CSS:', err);
  }
}

// Run minification
async function optimize() {
  await minifyJS();
  minifyCSS();
  console.log('Asset optimization complete!');
}

optimize(); 