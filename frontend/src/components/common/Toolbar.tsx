interface ToolbarProps {
    onAdd: () => void;
    addLabel?: string;
}

export default function Toolbar({ onAdd, addLabel = "New" }: ToolbarProps) {
    return (
        <div className="card-toolbar">
            <button className="btn btn-primary btn-sm" onClick={onAdd}>
                + {addLabel}
            </button>
        </div>
    );
}
