import type { RowData } from "@/lib/types";

export default function BilingualTable({ rows }: { rows: RowData[] }) {
  return (
    <table className="bilingual-table">
      <tbody>
        {rows.map((row, index) => (
          <tr key={index} className="verse-row">
            <td className="he" dangerouslySetInnerHTML={{ __html: row.heHtml }} />
            <td className="hu chapter-heading" dangerouslySetInnerHTML={{ __html: row.huHtml }} />
          </tr>
        ))}
      </tbody>
    </table>
  );
}

