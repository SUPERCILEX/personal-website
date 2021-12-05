#!/usr/bin/env bash
set -e
# Copied from https://github.com/helaili/jekyll-action/blob/f218514e3f6ecc859dc020a18be25fa9e951e449/entrypoint.sh

echo "Starting the Jekyll Action"

if [ -z "${JEKYLL_PAT}" ]; then
  echo "No token provided. Please set the JEKYLL_PAT environment variable."
  exit 1
fi

./.build/build_site.sh

cd build

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
git push --force "$remote_repo" master:$remote_branch && \
rm -fr .git && \
cd ..

echo -e "\nDeploying to Firebase Hosting"
./.build/node_modules/.bin/firebase deploy

exit $?
