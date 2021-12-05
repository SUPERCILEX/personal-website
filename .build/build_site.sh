#!/usr/bin/env bash
set -e

# Download latest resume
mkdir resume
curl -L --fail --output resume/AlexSaveau.pdf \
  --url https://docs.google.com/document/d/11sHvpwRaWoafEr2k8w5uXaJB0_VuMCtSxQNsErnpet0/export?format=pdf

# The jekyll-last-modified-at plugin uses Git history to determine when stuff has been
# updated. This works fine for blog posts, but not for fully templated pages that change
# when other pages change.
echo >> index.md
git -c "user.name=Hacker" -c "user.email=boo@hack.com" commit -am "Timestamp hack"
echo >> blog/index.md
(
  GIT_COMMITTER_DATE="$(git log -n 1 --pretty=format:%cd _posts/)"
  export GIT_COMMITTER_DATE
  git -c "user.name=Hacker" -c "user.email=boo@hack.com" commit -am "Timestamp hack" \
    --date "$GIT_COMMITTER_DATE"
)

(cd .build && npm ci)

if [ -n "${INPUT_JEKYLL_SRC}" ]; then
  JEKYLL_SRC=${INPUT_JEKYLL_SRC}
  echo "::debug ::Using parameter value ${JEKYLL_SRC} as a source directory"
elif [ -n "${SRC}" ]; then
  JEKYLL_SRC=${SRC}
  echo "::debug ::Using SRC environment var value ${JEKYLL_SRC} as a source directory"
else
  JEKYLL_SRC=$(find . -path ./vendor/bundle -prune -o -name '_config.yml' -exec dirname {} \;)
  echo "::debug ::Resolved ${JEKYLL_SRC} as a source directory"
fi

JEKYLL_ENV=production bundle exec jekyll build -s "$JEKYLL_SRC" -d build
echo "Jekyll build done"

# Make the firebase.json file available in Git, enabling human verification
cp firebase.json build/.firebase.json

# No need to have GitHub Pages to run Jekyll
touch build/.nojekyll

exit $?
