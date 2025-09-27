This is the Next.js MDX static-export site for `dreamaware.cc`.

## Quickstart
```bash
cd website
npm install --legacy-peer-deps
npm run build && npm run export
npx serve out
```

The static site is exported to `website/out/`.

## Notes
- Uses **Next 13.4.10** and **@next/mdx 13.4.10**.
- `output: 'export'`, `basePath` and `assetPrefix` are set for project pages at
 `https://diegocortes3211-design.github.io/dreamaware.cc/`.