export interface NavItem {
    label: string;
    path: string;
    icon: string;
    disabled?: boolean;
    badge?: string;
}

export interface NavGroup {
    label: string;
    icon: string;
    items: NavItem[];
    defaultOpen?: boolean;
}
