function formatLatex() {
  const input = document.getElementById('latex').value;
  const output = format(input);

  document.getElementById('result').innerHTML = output;
  navigator.clipboard.writeText(output);
}

function format(latex) {
  const docStartIndex = latex.indexOf('\\begin{document}');
  const ignored = latex.substring(0, docStartIndex);
  latex = latex.substring(docStartIndex)
      .replaceAll(/ +\n/gi, '\n')
      .replaceAll(/\. +/gi, '.\n')
      .replaceAll(/(\S)=/gi, '$1 =')
      .replaceAll(/=(\S)/gi, '= $1')
      .replaceAll(/& =/gi, '&=')
      .replaceAll(/(\S)\+/gi, '$1 +')
      .replaceAll(/\+(\S)/gi, '+ $1')
      .replaceAll(/(\S)-/gi, '$1 -')
      .replaceAll(/-(\S)/gi, '- $1')
      .replaceAll(/(\S)\\cdot/gi, '$1 \\cdot')
      .replaceAll(/\\cdot(\S)/gi, '\\cdot $1')
      .replaceAll(/\^{(\w)}/gi, '^$1');

  const lines = latex.split('\n');
  latex = '';

  let level = -1;
  for (let line of lines) {
    let hasBegin = line.includes('\\begin');
    let hasEnd = line.includes('\\end');

    if (hasEnd && !hasBegin) {
      level--;
    }

    const formattedLine = line.trimStart();

    if (formattedLine.length > 0) {
      latex += ' '.repeat(Math.max(0, level) * 4);
    }
    latex += formattedLine;
    latex += '\n';

    if (hasBegin && !hasEnd) {
      level++;
    }
  }

  return ignored + latex;
}
