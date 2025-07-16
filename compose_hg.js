// compose_hangul.js
const Hangul = require("hangul-js");

// Get input from command line arguments
const input = process.argv[2];

if (!input) {
  console.error('Usage: node compose_hangul.js "jamo_string"');
  process.exit(1);
}

// Compose the jamos into Hangul
const result = Hangul.assemble(input.split(""));
console.log(result);
