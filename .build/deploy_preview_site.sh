#!/bin/sh -e

echo "Starting the Jekyll Action"

./.build/build_site.sh

echo -e "\nDeploying to Firebase Hosting"
npm i firebase-tools
./node_modules/.bin/firebase hosting:channel:deploy "$BUILD_ID"

exit $?
