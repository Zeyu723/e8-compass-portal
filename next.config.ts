import type { NextConfig } from "next";

// Post-hackathon mode: the Python backend on the VPS is retired.
// /api/demo/sample-result is now a real Next.js route handler (see
// src/app/api/demo/sample-result/route.ts). Filesystem routes take
// precedence over rewrites, so no proxy entries are needed anymore.
const nextConfig: NextConfig = {};

export default nextConfig;
