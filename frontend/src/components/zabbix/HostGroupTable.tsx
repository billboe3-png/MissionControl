import DataTable, { Column } from "../common/DataTable";
import { ZabbixHostGroup } from "../../services/zabbix";

interface HostGroupTableProps {
    groups: ZabbixHostGroup[];
}

const columns: Column<ZabbixHostGroup>[] = [
    { key: "name", header: "Name" },
    { key: "host_count", header: "Hosts" },
];

export default function HostGroupTable({ groups }: HostGroupTableProps) {
    return <DataTable columns={columns} data={groups} emptyMessage="No host groups found" />;
}
