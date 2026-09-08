import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { findParashaBySlug, getParashaData, listAllParashaSlugs } from "@/lib/content";
import ParashaView from "@/components/ParashaView";

export function generateStaticParams() {
  return listAllParashaSlugs().map((parasha) => ({ parasha }));
}

export async function generateMetadata({ params }: { params: Promise<{ parasha: string }> }): Promise<Metadata> {
  const { parasha } = await params;
  const found = findParashaBySlug(parasha);
  if (!found) return {};
  return { title: `The Essentialist Torah – ${found.parasha}` };
}

export default async function ParashaPage({ params }: { params: Promise<{ parasha: string }> }) {
  const { parasha } = await params;
  const found = findParashaBySlug(parasha);
  if (!found) notFound();
  const data = getParashaData(found.book, found.parasha);

  return <ParashaView slug={data.slug} rows={data.rows} commentaries={data.commentaries} />;
}
