import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";
import tsParser from "@typescript-eslint/parser";

export default [
  {
    ignores: [
      "**/dist/**",
      "apps/web/dist/**",
      "**/node_modules/**",
      "**/artifacts/**",
      "**/.venv/**",
      "**/.build/**",
    ],
  },
  js.configs.recommended,
  ...pluginVue.configs["flat/recommended"],
  {
    files: ["apps/web/src/**/*.{ts,vue}", "apps/web/tests/**/*.{ts,vue}", "apps/web/*.{js,ts}"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        sourceType: "module",
      },
    },
    rules: {
      "vue/multi-word-component-names": "off",
      "vue/max-attributes-per-line": "off",
      "vue/singleline-html-element-content-newline": "off",
      "vue/attributes-order": "off",
      "vue/html-self-closing": "off",
      "no-unused-vars": "off",
      "no-undef": "off",
    },
  },
];
