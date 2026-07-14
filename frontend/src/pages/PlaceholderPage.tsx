interface PlaceholderPageProps {
    title: string;
    description?: string;
}

export default function PlaceholderPage({
    title,
    description = "This module is planned for a future sprint.",
}: PlaceholderPageProps) {
    return (
        <div className="placeholder-page">
            <span className="placeholder-icon">🚧</span>
            <h2 className="placeholder-title">{title}</h2>
            <p className="placeholder-description">{description}</p>
        </div>
    );
}
