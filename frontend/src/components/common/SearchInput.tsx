interface SearchInputProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

export default function SearchInput({
    value,
    onChange,
    placeholder = "Search…",
    className = "",
}: SearchInputProps) {
    return (
        <div className={`search-input ${className}`.trim()}>
            <span className="search-input-icon">🔍</span>
            <input
                type="text"
                className="search-input-field"
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />
            {value && (
                <button
                    className="search-input-clear"
                    onClick={() => onChange("")}
                    title="Clear"
                >
                    ×
                </button>
            )}
        </div>
    );
}
