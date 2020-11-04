#!/bin/sh -e

echo "::debug ::Starting install"
bundle config path vendor/bundle
bundle install

(cd .build && npm ci)
echo "::debug ::Completed install"

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

# Run the build twice so webp generation can work on the resized images
# The webp plugin performs caching based file modification timestamps.
test -d "build/assets" && find build/assets -type f -exec touch {} + || true
JEKYLL_ENV=production bundle exec jekyll build -s ${JEKYLL_SRC} -d build
test -d "build/assets" && find build/assets -type f -exec touch {} + || true
JEKYLL_ENV=production bundle exec jekyll build -s ${JEKYLL_SRC} -d build
echo "Jekyll build done"

echo "Generating Firebase config"
python3 .build/firebase_redirect_inliner.py
# The .firebase.json file will be available in Git, enabling human verification
cp firebase.json build/.firebase.json

# No need to have GitHub Pages to run Jekyll
touch build/.nojekyll

exit $?
