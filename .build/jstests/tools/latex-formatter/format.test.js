const formatting = require('../../../../tools/latex-formatter/index');

test('empty document does nothing', () => {
  expect(formatting.format()).toBe('');
  expect(formatting.format('')).toBe('');
});

test('document without begin{document} does nothing', () => {
  const document = `blah blah
\\begin{question}
blah`;

  expect(formatting.format(document)).toBe(document);
});

test('imports are ignored', () => {
  const document = `blah-blah
    foobar

\\begin{document}
stuff
\\end{document}
`;

  expect(formatting.format(document)).toBe(document);
});

test('environments are indented', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}
    \\begin{b}
    \\begin{c}
    \\end{c}
    \\begin{e}
    \\end{e}
    \\end{b}
    \\end{a}

    \\begin{d}
    \\end{d}
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    \\begin{b}
        \\begin{c}
        \\end{c}
        \\begin{e}
        \\end{e}
    \\end{b}
\\end{a}

\\begin{d}
\\end{d}
\\end{document}
`);
});

// TODO fix
test.skip('minted code is de-indented', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}
    \\begin{minted}{python}
    def foo():
        1 + 1
    \\end{minted}
    \\end{a}
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    \\begin{minted}{python}
def foo():
    1 + 1
    \\end{minted}
\\end{a}
\\end{document}
`);
});

test('minted code isn\'t modified', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}
    \\begin{minted}{python}
1+1-1==1
    \\end{minted}
    \\end{a}
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    \\begin{minted}{python}
1+1-1==1
    \\end{minted}
\\end{a}
\\end{document}
`);
});

test('compressed math is formatted correctly', () => {
  const math = 'a=b+1-2^{5}\\cdot\\log(2)';

  expect(formatting.format(`
    \\begin{document}
    $${math}$
    $
    ${math}
    $

    $$${math}$$
    $$
    ${math}
    $$

    \\begin{align*}
    ${math}
    \\end{align*}
    \\end{document}`)).toBe(`\\begin{document}
$a = b + 1 - 2^5 \\cdot \\log(2)$
$
a = b + 1 - 2^5 \\cdot \\log(2)
$

$$a = b + 1 - 2^5 \\cdot \\log(2)$$
$$
a = b + 1 - 2^5 \\cdot \\log(2)
$$

\\begin{align*}
    a = b + 1 - 2^5 \\cdot \\log(2)
\\end{align*}
\\end{document}
`);
});

test('uncompressed math is formatted correctly', () => {
  expect(formatting.format(`
    \\begin{document}
    $a   =  b  + 1  -   2^{5}   \\cdot         \\log(2)$
    \\end{document}`)).toBe(`\\begin{document}
$a = b + 1 - 2^5 \\cdot \\log(2)$
\\end{document}
`);
});

test('math is ignored outside of equation blocks', () => {
  const math = 'a=b+1-2^{5}\\cdot\\log(2)';

  expect(formatting.format(`
    \\begin{document}
    \\begin{a}
    $$blah$$
    \\\\$blah$
    \\$${math}\\$
    \\end{a}
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    $$blah$$
    \\\\$blah$
    \\$${math}\\$
\\end{a}
\\end{document}
`);
});

test('trailing whitespace is stripped', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}  
    blah   
    \\end{a}  
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    blah
\\end{a}
\\end{document}
`);
});

test('sentences are separated by a new line', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}  
    'a.b.c.' is cool. So is this. Blah.   
    \\end{a}  
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    'a.b.c.' is cool.
    So is this.
    Blah.
\\end{a}
\\end{document}
`);
});

test('known abbreviations aren\'t treated as sentence breaks', () => {
  expect(formatting.format(`
    \\begin{document}
    \\begin{a}  
    I eat italian food, i.e. pasta. E.g. blah.
    \\end{a}  
    \\end{document}`)).toBe(`\\begin{document}
\\begin{a}
    I eat italian food, i.e. pasta.
    E.g. blah.
\\end{a}
\\end{document}
`);
});

test('dots inside equation blocks are ignored', () => {
  expect(formatting.format(`
    \\begin{document}
    $\\forall f. (...)$
    $$\\forall f. (...)$$
    \\begin{align*}
    \\forall f. (...)
    \\end{align*}
    \\end{document}`)).toBe(`\\begin{document}
$\\forall f. (...)$
$$\\forall f. (...)$$
\\begin{align*}
    \\forall f. (...)
\\end{align*}
\\end{document}
`);
});

test('minus sign is not formatted when used as negation', () => {
  expect(formatting.format(`
    \\begin{document}
    $a - b, a-b, a- b, a -b$
    $$blah$$
    $-1$
    \\end{document}`)).toBe(`\\begin{document}
$a - b, a - b, a - b, a -b$
$$blah$$
$-1$
\\end{document}
`);
});

test('minus sign is not formatted when against parentheses', () => {
  expect(formatting.format(`
    \\begin{document}
    $-1$
    $(-1)$
    $[-1]$
    $|-1|$
    $x^{-1}$
    $--1$
    \\end{document}`)).toBe(`\\begin{document}
$-1$
$(-1)$
$[-1]$
$|-1|$
$x^{-1}$
$--1$
\\end{document}
`);
});

test('&= is kept together', () => {
  expect(formatting.format(`
    \\begin{document}
    $&=foo$
    $&= foo$
    \\end{document}`)).toBe(`\\begin{document}
$&= foo$
$&= foo$
\\end{document}
`);
});

test('=\\; is kept together', () => {
  expect(formatting.format(`
    \\begin{document}
    $=\\;foo$
    $=\\; foo$
    \\end{document}`)).toBe(`\\begin{document}
$=\\;foo$
$=\\; foo$
\\end{document}
`);
});

test('put space before \\ character', () => {
  expect(formatting.format(`
    \\begin{document}
    $\\ln(e)$
    $blah\\\\$
    $a\\ln(e)$
    $a\\;b$
    $&\\geq$
    $\\sum_{i=1}^\\infinity$
    $blah \\\\ blah$
    $-\\ln(e)$
    $1 - (\\ln(e))$
    $1 - [\\ln(e)]$
    $1 - |\\ln(e)|$
    \\end{document}`)).toBe(`\\begin{document}
$\\ln(e)$
$blah \\\\$
$a \\ln(e)$
$a \\;b$
$&\\geq$
$\\sum_{i = 1}^\\infinity$
$blah \\\\ blah$
$-\\ln(e)$
$1 - (\\ln(e))$
$1 - [\\ln(e)]$
$1 - |\\ln(e)|$
\\end{document}
`);
});
