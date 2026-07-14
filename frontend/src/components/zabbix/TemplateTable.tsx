import DataTable, { Column } from "../common/DataTable";
import { ZabbixTemplate } from "../../services/zabbix";

interface TemplateTableProps {
    templates: ZabbixTemplate[];
}

const columns: Column<ZabbixTemplate>[] = [
    { key: "name", header: "Name" },
    { key: "hosts_count", header: "Linked Hosts" },
];

export default function TemplateTable({ templates }: TemplateTableProps) {
    return <DataTable columns={columns} data={templates} emptyMessage="No templates found" />;
}
