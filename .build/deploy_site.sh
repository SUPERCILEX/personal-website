#!/bin/sh
set -e
# Copied from https://github.com/helaili/jekyll-action/blob/f218514e3f6ecc859dc020a18be25fa9e951e449/entrypoint.sh

echo "Starting the Jekyll Action"

if [ -z "${JEKYLL_PAT}" ]; then
  echo "No token provided. Please set the JEKYLL_PAT environment variable."
  exit 1
fi

echo "::debug ::Starting bundle install"
bundle config path vendor/bundle
bundle install
echo "::debug ::Completed bundle install"

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
JEKYLL_ENV=production bundle exec jekyll build -s ${JEKYLL_SRC} -d build
JEKYLL_ENV=production bundle exec jekyll build -s ${JEKYLL_SRC} -d build
echo "Jekyll build done"

echo "Generating Firebase config"
python3 .build/firebase_redirect_inliner.py
# The .firebase.json file will be available in Git, enabling human verification
cp firebase.json build/.firebase.json

cd build

# No need to have GitHub Pages to run Jekyll
touch .nojekyll

# Is this a regular repo or an org.github.io type of repo
case "${GITHUB_REPOSITORY}" in
  *.github.io) remote_branch="master" ;;
  *)           remote_branch="built-site" ;;
esac

if [ "${GITHUB_REF}" = "refs/heads/${remote_branch}" ]; then
  echo "Cannot publish on branch ${remote_branch}"
  exit 1
fi

echo "Publishing to ${GITHUB_REPOSITORY} on branch ${remote_branch}"
echo "::debug ::Pushing to https://${JEKYLL_PAT}@github.com/${GITHUB_REPOSITORY}.git"

remote_repo="https://${JEKYLL_PAT}@github.com/${GITHUB_REPOSITORY}.git" && \
git init && \
git config user.name "${GITHUB_ACTOR}" && \
git config user.email "${GITHUB_ACTOR}@users.noreply.github.com" && \
git add . && \
git commit -m "jekyll build from Action ${GITHUB_SHA}" && \
git push --force $remote_repo master:$remote_branch && \
rm -fr .git && \
cd ..

echo -e "\nDeploying to Firebase Hosting"
npm i firebase-tools
./node_modules/.bin/firebase deploy

exit $?