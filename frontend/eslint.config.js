import tseslint from "typescript-eslint";

export default tseslint.config(
    {
        ignores: [
            "node_modules/**",
            "coverage/**",
            "playwright-report/**",
            "test-results/**",
        ],
    },
    ...tseslint.configs.strict,
    {
        rules: {
            // Map lookups right after a has()/set() are clearer with `!` than with dead branches.
            "@typescript-eslint/no-non-null-assertion": "off",
        },
    },
);
