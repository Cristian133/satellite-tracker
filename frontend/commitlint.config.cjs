// Config de commitlint (https://commitlint.js.org), consumida por el hook
// `commitlint` local en .pre-commit-config.yaml (stage commit-msg).
// Extensión .cjs a propósito: package.json tiene "type": "module", así que
// un .js acá sería tratado como ESM por Node.
module.exports = {
  extends: ["@commitlint/config-conventional"],
};
