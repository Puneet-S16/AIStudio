function validateJSON() {
  const input = document.getElementById('jsonInput').value;
  const resultDiv = document.getElementById('result');
  const errorDiv = document.getElementById('errorHighlight');
  
  try {
    JSON.parse(input);
    resultDiv.innerHTML = '<div class="text-green-400">✅ Valid JSON</div>';
    errorDiv.innerHTML = '';
  } catch (e) {
    const errorPos = e.message.match(/position (\d+)/);
    if (errorPos) {
      const pos = parseInt(errorPos[1]);
      const lines = input.split('\n');
      let line = 0, col = 0;
      
      for (let i = 0; i < lines.length; i++) {
        if (pos > lines[i].length) {
          pos -= lines[i].length + 1;
          line++;
        } else {
          col = pos;
          line = i;
          break;
        }
      }
      
      const errorHtml = `
        <div class="flex items-start gap-2 mb-3">
          <i class="material-icons text-red-400">error</i>
          <div>
            <strong class="text-red-400">❌ Error at line ${line + 1}, column ${col + 1}</strong>
            <div class="text-gray-300 mt-1">${e.message}</div>
          </div>
        </div>
      `;
      
      resultDiv.innerHTML = errorHtml;
      errorDiv.innerHTML = `<pre>${input.split('\n').map((line, i) => 
        i === line ? `<span class="text-red-400">${line}</span>` : line
      ).join('\n')}</pre>`;
      
      document.getElementById('jsonInput').style.outline = '2px dashed red';
    } else {
      resultDiv.innerHTML = `<div class="text-red-400">❌ ${e.message}</div>`;
      errorDiv.innerHTML = '';
    }
  }
}