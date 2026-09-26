import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/types.ts', 'src/frontmatter.ts', 'src/validator.ts'],
  format: ['esm'],
  dts: true,
  splitting: false,
  sourcemap: true,
  treeshake: true,
  clean: true,
  target: 'es2022',
  tsconfig: 'tsconfig.build.json',
});
