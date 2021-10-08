#!/bin/bash
# A helper script to compile the DIRAC WebApp without running the full docker
# build/packaging process.

set -ex

SENCHA="/opt/dirac/sbin/Sencha/Cmd/sencha"
EXTJS="/opt/dirac/extjs/ext-6.2.0"
TEMPLATE_DIR="/opt/dirac/management/dirac-distribution/CompileTemplates"
WEBAPP_BASE="/opt/dirac/WebAppDIRAC"
STATIC_BASE="${WEBAPP_BASE}/WebApp/static"
APP_BASE="${STATIC_BASE}/DIRAC"

CLASSPATH_RAW=(
  "${STATIC_BASE}/core/js/utils"
  "${STATIC_BASE}/core/js/core"
  "${EXTJS}/build/ext-all-debug.js"
  "${EXTJS}/build/packages/ux/classic/ux-debug.js"
  "${EXTJS}/build/packages/charts/classic/charts-debug.js")
STATICS=(
  "packages" "classic" "ext-all.js" "ext-all-debug.js"
  "packages/ux/classic/ux-debug.js")

# We need classpath as a comma seperated string not an array
function fixClasspath() {
  local IFS=","
  CLASSPATH="${CLASSPATH_RAW[*]}"
}
fixClasspath

# Compress all source files in a given directory tree
function compressRes() {
  TDIR=$1
  for FTYPE in js css; do
    find "${TDIR}" -iname "*.${FTYPE}" -exec sh -c 'gzip -9 < "$1" > "$1.gz"' shell {} \;
  done
}

# Build a single app by name
function buildApp() {
  APP=$1
  BUILD_DIR="${APP_BASE}/${APP}/build"
  mkdir -p "${BUILD_DIR}"
  sed -e "s#%APP_LOCATION%#DIRAC.${APP}.classes.${APP}#" \
    "${TEMPLATE_DIR}/app.tpl" > "${BUILD_DIR}/app.tpl"
  ${SENCHA} -sdk "${EXTJS}" compile \
    -classpath "${CLASSPATH},${APP_BASE}/${APP}/classes" \
    page -name=page \
    -input-file "${BUILD_DIR}/app.tpl" \
    -out "${BUILD_DIR}/index.html" \
    and restore page and exclude -not -namespace "Ext.dirac.*,DIRAC.*" \
    and concat -yui "${BUILD_DIR}/${APP}.js"
  compressRes "${APP_BASE}/${APP}"
}

# Build the extjs core lib
function buildCore() {
  mkdir -p ${STATIC_BASE}/core/build
  ${SENCHA} -sdk "${EXTJS}" compile -classpath "${CLASSPATH}" \
    page -yui -input-file "${TEMPLATE_DIR}/core.tpl" \
    -out "${STATIC_BASE}/core/build/index.html"
  compressRes "${STATIC_BASE}/core/build"
}

# Copy static files
function buildStatic() {
  mkdir -p ${STATIC_BASE}/extjs
  for SFILE in "${STATICS[@]}"; do
    cp -uR "${EXTJS}/build/${SFILE}" "${STATIC_BASE}/extjs"
  done
  compressRes "${STATIC_BASE}/extjs"
}

if [ "$1" == "clean" ]; then
  rm -Rf ${STATIC_BASE}/extjs ${STATIC_BASE}/core/build ${APP_BASE}/*/build
  find ${APP_BASE} -iname '*.gz' -delete
else
  # Build everything, order is not too important
  buildStatic
  buildCore
  for APP_DIR in "${APP_BASE}"/*; do
    buildApp "$(basename "$APP_DIR")"
  done
fi
