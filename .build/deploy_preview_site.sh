#!/usr/bin/env bash
set -e

echo "Starting the Jekyll Action"

./.build/build_site.sh

echo -e "\nDeploying to Firebase Hosting"
./.build/node_modules/.bin/firebase hosting:channel:deploy "$GITHUB_REF_NAME"

exit $?
