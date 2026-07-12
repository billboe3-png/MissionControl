const API = "/api/v1/parking-lot";

export interface ParkingLotCreateInput {
    title: string;
    description?: string;
    priority?: string;
    status?: string;
    owner?: string;
    category?: string;
    labels?: string;
    target_sprint?: string;
    created_by?: string;
}

export interface ParkingLotUpdateInput {
    title?: string;
    description?: string;
    priority?: string;
    status?: string;
    owner?: string;
    category?: string;
    labels?: string;
    target_sprint?: string;
    archived?: boolean;
}

export interface ParkingLotItemData {
    id: number;
    title: string;
    description: string | null;
    priority: string;
    status: string;
    owner: string | null;
    category: string | null;
    labels: string | null;
    target_sprint: string | null;
    archived: boolean;
    created_by: string | null;
    created_at: string;
    updated_at: string;
}

export interface ParkingLotListData {
    count: number;
    items: ParkingLotItemData[];
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json();
}

export const parkingLotApi = {
    async list(): Promise<ParkingLotListData> {
        const response = await fetch(API);
        return handleResponse<ParkingLotListData>(response);
    },

    async create(data: ParkingLotCreateInput): Promise<ParkingLotItemData> {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<ParkingLotItemData>(response);
    },

    async update(
        id: number,
        data: ParkingLotUpdateInput,
    ): Promise<ParkingLotItemData> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<ParkingLotItemData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};
