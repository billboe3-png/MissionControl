import DataTable, { Column } from "../common/DataTable";
import { ZabbixItem } from "../../services/zabbix";

interface ItemTableProps {
    items: ZabbixItem[];
}

const columns: Column<ZabbixItem>[] = [
    { key: "name", header: "Name" },
    { key: "key_", header: "Key" },
    { key: "type", header: "Type" },
    { key: "last_value", header: "Last Value" },
    { key: "host", header: "Host" },
];

export default function ItemTable({ items }: ItemTableProps) {
    return <DataTable columns={columns} data={items} emptyMessage="No items found" />;
}
