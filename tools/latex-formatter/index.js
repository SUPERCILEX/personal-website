function formatLatex() {
    const input = document.getElementById('latex').value;
    const output = format(input);

    document.getElementById('result').innerHTML = output;
    navigator.clipboard.writeText(output);
}

function format(latex) {
    return latex
        .replaceAll(/ +\n/gi, '\n')
        .replaceAll(/\. +/gi, '.\n')
        .replaceAll(/(\S)=/gi, '$1 =').replaceAll(/=(\S)/gi, '= $1')
        .replaceAll(/& =/gi, '&=')
        .replaceAll(/(\S)\+/gi, '$1 +').replaceAll(/\+(\S)/gi, '+ $1')
        .replaceAll(/(\S)-/gi, '$1 -').replaceAll(/-(\S)/gi, '- $1')
        .replaceAll(/(\S)\\cdot/gi, '$1 \\cdot').replaceAll(/\\cdot(\S)/gi, '\\cdot $1')
        .replaceAll(/\^{(\w)}/gi, '^$1');
}
