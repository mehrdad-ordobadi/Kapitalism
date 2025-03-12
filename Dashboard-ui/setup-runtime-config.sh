#!/bin/sh
mkdir -p /app/public
cat > /app/public/runtime-config.js << EOF
window.ENV = {
  API_BASE: "${REACT_APP_API_HOST}"
};
console.log("Runtime config loaded with API_BASE: ${REACT_APP_API_HOST}");
EOF