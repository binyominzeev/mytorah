import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "The Essentialist Torah",
    short_name: "EssTorah",
    description: "The Essentialist Torah",
    start_url: "/",
    display: "standalone",
    background_color: "#14161d",
    theme_color: "#14161d",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
