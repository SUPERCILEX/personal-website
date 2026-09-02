function formatLatex() {
  const input = document.getElementById('latex').value;
  const output = format(input);

  document.getElementById('result').innerHTML = output;
  navigator.clipboard.writeText(output);
}

function format(latex) {
  if (!latex) {
    return '';
  }
  latex = latex.trim();

  const docStartIndex = latex.indexOf('\\begin{document}');
  if (docStartIndex < 0) {
    return latex;
  }

  const ignored = latex.substring(0, docStartIndex);
  latex = latex.substring(docStartIndex);

  const lines = latex.split('\n');
  latex = '';

  let equationStart = -1;
  let environmentStack = [];
  for (let line of lines) {
    let hasBegin = line.includes('\\begin');
    let hasEnd = line.includes('\\end');

    if (hasEnd && !hasBegin) {
      environmentStack.pop();
    }

    const insideMintedEnvironment = environmentStack.some(
        s => ['minted'].includes(s.environment));
    const insideEquationEnvironment = environmentStack.some(
        s => ['align*'].includes(s.environment));

    let formattedLine;
    if (insideMintedEnvironment) {
      formattedLine = line.trimEnd();
    } else {
      formattedLine = line.trim();
    }

    if (formattedLine.length > 0) {
      const indent = ' '.repeat(Math.max(0, environmentStack.length - 1) * 4);

      if (insideEquationEnvironment) {
        formattedLine = formatMath(formattedLine);
      } else {
        let i = 0;
        for (let c of formattedLine) {
          const beforeLength = formattedLine.length;
          const prevChar = formattedLine[i - 1];
          const prevPrevChar = formattedLine[i - 2];

          if (c === '$' && (prevChar !== '\\' || prevPrevChar === '\\')) {
            if (prevChar === '$') {
              if (equationStart !== -1) {
                equationStart++;
              }
            } else {
              if (equationStart === -1) {
                equationStart = i + 1;
              } else {
                formattedLine = replace(equationStart, i, formattedLine,
                    formatMath(formattedLine.substring(equationStart, i)));
                equationStart = -1;
              }
            }
          }
          if (equationStart === -1 && c === ' ' && prevChar === '.') {
            const lower = formattedLine.toLowerCase();
            const isAbbreviation = lower.indexOf('i.e.') === i - 4
                || lower.indexOf('e.g.') === i - 4;

            if (!isAbbreviation) {
              formattedLine = replace(i, i + 1, formattedLine, '\n' + indent);
            }
          }

          i += 1 + formattedLine.length - beforeLength;
        }

        if (equationStart !== -1) {
          formattedLine = replace(0, formattedLine.length, formattedLine,
              formatMath(formattedLine));
          equationStart = 0;
        }
      }

      if (!insideMintedEnvironment) {
        latex += indent;
      }
    }

    latex += formattedLine;
    latex += '\n';

    if (hasBegin && !hasEnd) {
      const begin = '\\begin{';
      let environment = line.substring(line.indexOf(begin) + begin.length);
      environment = environment.substring(0, environment.indexOf('}'));

      environmentStack.push({
        environment,
      });
    }
  }

  return ignored + latex;
}

function formatMath(math) {
  return math
      .replace(/\s+=\s+/gi, '=')
      .replace(/(\S)=/gi, '$1 =')
      .replace(/=(\S)/gi, '= $1')
      .replace(/\s+\+\s+/gi, '+')
      .replace(/(\S)\+/gi, '$1 +')
      .replace(/\+(\S)/gi, '+ $1')
      .replace(/\s+-\s+/gi, '-')
      .replace(/([^({\[|\- ])-(\S)/gi, '$1 - $2')
      .replace(/([^({\[|\- ])-/gi, '$1 -')
      .replace(/\s+\\cdot\s+/gi, '\\cdot')
      .replace(/(\S)\\cdot/gi, '$1 \\cdot')
      .replace(/,(\S)/gi, ', $1')
      .replace(/\\,\s/gi, '\\,')
      .replace(/[^\\],(\S)/gi, '$1, $2')
      .replace(/([^({\[|&\-^\\ ])\\([^}])/gi, '$1 \\$2')
      .replace(/\. \\bar/gi, '.\\bar')
      .replace(/\\cdot(\S)/gi, '\\cdot $1')
      .replace(/\^{(\w)}/gi, '^$1')
      .replace(/_{(\w)}/gi, '_$1')
      .replace(/& =/gi, '&=')
      .replace(/: =/gi, ':=')
      .replace(/= \\;/gi, '=\\;');
}

function replace(start, end, existing, replacement) {
  return existing.substring(0, start) + replacement + existing.substring(end);
}

try {
  module.exports = exports = {
    format,
  };
} catch (ignored) {
}
