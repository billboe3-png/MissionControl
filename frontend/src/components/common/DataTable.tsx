import { ReactNode } from "react";

export interface Column<T> {
    key: string;
    header: string;
    render?: (row: T) => ReactNode;
    className?: string;
}

interface DataTableProps<T> {
    columns: Column<T>[];
    data: T[];
    onRowClick?: (row: T) => void;
    emptyMessage?: string;
    keyExtractor?: (row: T) => string | number;
}

export default function DataTable<T extends object>({
    columns,
    data,
    onRowClick,
    emptyMessage = "No data available",
    keyExtractor,
}: DataTableProps<T>) {
    if (data.length === 0) {
        return (
            <div className="data-table-empty">
                <p>{emptyMessage}</p>
            </div>
        );
    }

    return (
        <div className="data-table-wrapper">
            <table className="data-table">
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th key={col.key} className={col.className}>
                                {col.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, i) => (
                        <tr
                            key={keyExtractor ? keyExtractor(row) : i}
                            onClick={onRowClick ? () => onRowClick(row) : undefined}
                            className={onRowClick ? "clickable" : undefined}
                        >
                            {columns.map((col) => (
                                <td key={col.key} className={col.className}>
                                    {col.render
                                        ? col.render(row)
                                        : String((row as Record<string, unknown>)[col.key] ?? "")}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
