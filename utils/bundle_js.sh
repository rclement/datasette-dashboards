#!/bin/bash

./node_modules/.bin/rollup node_modules/vega/build/vega.min.js --file datasette_dashboards/static/vega.min.js
./node_modules/.bin/rollup node_modules/vega-embed/build/vega-embed.min.js --file datasette_dashboards/static/vega-embed.min.js
./node_modules/.bin/rollup node_modules/vega-lite/build/vega-lite.min.js --file datasette_dashboards/static/vega-lite.min.js