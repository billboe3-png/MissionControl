import { ZabbixMap } from "../../services/zabbix";

interface MapCardProps {
    map: ZabbixMap;
}

export default function MapCard({ map }: MapCardProps) {
    return (
        <div className="ad-info-card">
            <h4>{map.name}</h4>
            <p><strong>Dimensions:</strong> {map.width} x {map.height}</p>
            <p><strong>Elements:</strong> {map.elements}</p>
        </div>
    );
}
